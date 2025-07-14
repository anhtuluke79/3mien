import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import joblib
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)
from itertools import combinations, permutations
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ============= CONFIG ============
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_REPO_PATH = "/path/to/3mien" # Đường dẫn repo local (sửa lại theo máy bạn)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ============= TIỆN ÍCH ============
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]
def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]
def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))
def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())
def get_can_chi_ngay(year, month, day):
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    can = can_list[(jd + 9) % 10]
    chi = chi_list[(jd + 1) % 12]
    return f"{can} {chi}"
def sinh_so_hap_cho_ngay(can_chi_str):
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code: return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j: ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can, "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"), "so_menh": so_menh,
        "so_hap_list": so_ghep, "so_ghép": sorted(list(ket_qua))
    }
def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else: so_hap_can, so_menh = "?", "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n- Số hạp ngày: {so_hap_ngay}"
    )
    return text
def chot_so_format(can_chi, sohap_info, today_str):
    if not sohap_info or not sohap_info.get("so_hap_list"):
        return "Không đủ dữ liệu phong thủy để chốt số hôm nay!"
    d = [sohap_info['so_menh']] + sohap_info['so_hap_list']
    chams = ','.join(d)
    dan_de = []
    for x in d:
        for y in d:
            dan_de.append(x + y)
    dan_de = sorted(set(dan_de))
    lo = []
    for x in d:
        for y in d:
            if x != y: lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n*Chốt số 3 miền ngày {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text

# ==== DỰ ĐOÁN AI ML/RF ====
def predict_xsmb_rf():
    model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(model_path) or not os.path.exists(csv_path):
        return "❌ Model hoặc dữ liệu xsmb.csv chưa có trên server!"
    model = joblib.load(model_path)
    df = pd.read_csv(csv_path)
    features = []
    for i in range(-3, 0):
        day = df.iloc[i]
        features += [int(day['DB'][-2:]), int(day['G1'][-2:])]
    X_pred = [features]
    y_pred = model.predict(X_pred)
    return f"🤖 Thần tài dự đoán giải đặc biệt hôm nay (2 số cuối):\n👉 {str(y_pred[0]).zfill(2)}\n(ML: Random Forest)"

# =================== MENU & CALLBACK NHIỀU TẦNG ===================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 Train & Lưu model", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬆️ Upload model lên Github", callback_data="admin_upload_model")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên Github", callback_data="admin_upload_csv")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    # ADMIN
    if query.data == "admin_menu":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu quản trị.")
            return
        await admin_menu(update, context)
        return
    if query.data == "admin_train_rf":
        await query.edit_message_text("⏳ Đang train model RF (demo)...")
        await query.message.reply_text("✅ Đã train xong, lưu rf_model_xsmb.pkl (demo).")
        return
    if query.data == "admin_upload_model":
        await query.edit_message_text("⏳ Đang upload model rf_model_xsmb.pkl lên Github...")
        try:
            os.chdir(GITHUB_REPO_PATH)
            subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload file model rf_model_xsmb.pkl lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload model: {e}")
        return
    if query.data == "admin_upload_csv":
        await query.edit_message_text("⏳ Đang upload xsmb.csv lên Github...")
        try:
            os.chdir(GITHUB_REPO_PATH)
            subprocess.run(["git", "add", "xsmb.csv"], check=True)
            subprocess.run(["git", "commit", "-m", "update xsmb.csv"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload: {e}")
        return
    # ML PREDICT
    if query.data == "ml_predict":
        await query.edit_message_text("⏳ Đang dự đoán bằng AI Thần tài (Random Forest)...")
        result = predict_xsmb_rf()
        await query.message.reply_text(result)
        await menu(update, context)
        return
    # GHÉP XIÊN
    if query.data == "menu_ghepxien":
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="ghepxien_2"),
             InlineKeyboardButton("Xiên 3", callback_data="ghepxien_3"),
             InlineKeyboardButton("Xiên 4", callback_data="ghepxien_4")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data.startswith("ghepxien_"):
        context.user_data.clear()
        do_dai = int(query.data.split("_")[1])
        context.user_data['wait_for_xien_input'] = do_dai
        await query.edit_message_text(f"Nhập dãy số để ghép xiên {do_dai} (cách nhau dấu cách hoặc phẩy):")
        return
    # GHÉP CÀNG, ĐẢO SỐ
    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Càng 3D", callback_data="ghepcang_3d"),
             InlineKeyboardButton("Càng 4D", callback_data="ghepcang_4d"),
             InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại càng hoặc đảo số:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "ghepcang_3d":
        context.user_data.clear()
        context.user_data['wait_for_cang3d_numbers'] = True
        await query.edit_message_text("Nhập dãy số cần ghép (cách nhau phẩy hoặc dấu cách, ví dụ: 23 32 28 82 ...):")
        return
    if query.data == "ghepcang_4d":
        context.user_data.clear()
        context.user_data['wait_for_cang4d_numbers'] = True
        await query.edit_message_text("Nhập dãy số cần ghép (3 chữ số, cách nhau phẩy hoặc dấu cách, ví dụ: 123 234 345 ...):")
        return
    if query.data == "daoso":
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text("Nhập một số hoặc dãy số (VD: 123 hoặc 1234):")
        return
    # PHONG THỦY
    if query.data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("Theo ngày dương (YYYY-MM-DD)", callback_data="phongthuy_ngay_duong")],
            [InlineKeyboardButton("Theo can chi (VD: Giáp Tý)", callback_data="phongthuy_ngay_canchi")],
            [InlineKeyboardButton("Ngày hiện tại", callback_data="phongthuy_ngay_today")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🔮 Bạn muốn tra phong thủy theo kiểu nào?", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "phongthuy_ngay_duong":
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_duong'] = True
        await query.edit_message_text("📅 Nhập ngày dương lịch (YYYY-MM-DD):")
        return
    if query.data == "phongthuy_ngay_canchi":
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_canchi'] = True
        await query.edit_message_text("📜 Nhập can chi (ví dụ: Giáp Tý):")
        return
    if query.data == "phongthuy_ngay_today":
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        can_chi = get_can_chi_ngay(y, m, d)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        today_str = f"{d:02d}/{m:02d}/{y}"
        text = phong_thuy_format(can_chi, sohap_info, is_today=True, today_str=today_str)
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    # CHỐT SỐ
    if query.data == "menu_chotso":
        keyboard = [
            [InlineKeyboardButton("Chốt số hôm nay", callback_data="chot_so_today")],
            [InlineKeyboardButton("Chốt số theo ngày", callback_data="chot_so_ngay")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn cách chốt số:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "chot_so_today":
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        can_chi = get_can_chi_ngay(y, m, d)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        today_str = f"{d:02d}/{m:02d}/{y}"
        text = chot_so_format(can_chi, sohap_info, today_str)
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    if query.data == "chot_so_ngay":
        context.user_data.clear()
        context.user_data['wait_chot_so_ngay'] = True
        await query.edit_message_text("📅 Nhập ngày dương lịch muốn chốt số:\n- Định dạng đầy đủ: YYYY-MM-DD (vd: 2025-07-11)\n- Hoặc chỉ ngày-tháng: DD-MM (vd: 11-07, sẽ lấy năm hiện tại)")
        return
    # ỦNG HỘ
    if query.data == "ungho":
        keyboard = [
            [InlineKeyboardButton("Hiển thị mã QR Vietcombank", callback_data="qr_ungho")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        text = (
            "💗 *Ủng hộ bot*\n\n"
            "- Vietcombank: 0071003914986 (Trương Anh Tú)\n"
            "- Momo: 0904123123 (Tú)\n"
            "- Xin cảm ơn sự ủng hộ của bạn để bot tiếp tục phát triển!\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "qr_ungho":
        with open("qr_vcb.png", "rb") as f:
            await query.message.reply_photo(photo=InputFile(f), caption="Quét mã QR để ủng hộ 💗\nXin cảm ơn!")
        return
    if query.data == "main_menu":
        await menu(update, context)
        return

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ghép càng 3D
    if context.user_data.get('wait_for_cang3d_numbers'):
        arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
        if not arr:
            await update.message.reply_text("Vui lòng nhập dãy số (ví dụ: 23 32 28 ...)")
            return
        context.user_data['cang3d_numbers'] = arr
        context.user_data['wait_for_cang3d_numbers'] = False
        context.user_data['wait_for_cang3d_cangs'] = True
        await update.message.reply_text("Nhập các càng muốn ghép (cách nhau phẩy hoặc dấu cách, ví dụ: 1 2 3):")
        return
    if context.user_data.get('wait_for_cang3d_cangs'):
        cang_list = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
        if not cang_list:
            await update.message.reply_text("Vui lòng nhập các càng (ví dụ: 1 2 3):")
            return
        numbers = context.user_data.get('cang3d_numbers', [])
        result = []
        for c in cang_list:
            for n in numbers:
                result.append(c + n)
        await update.message.reply_text(f"Kết quả ghép càng 3D ({len(result)} số):\n" + ', '.join(result))
        context.user_data['wait_for_cang3d_cangs'] = False
        context.user_data['cang3d_numbers'] = []
        await menu(update, context)
        return
    # Ghép càng 4D
    if context.user_data.get('wait_for_cang4d_numbers'):
        arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
        if not arr or not all(len(n) == 3 for n in arr):
            await update.message.reply_text("Vui lòng nhập các số 3 chữ số, cách nhau phẩy hoặc dấu cách (ví dụ: 123 234 ...)")
            return
        context.user_data['cang4d_numbers'] = arr
        context.user_data['wait_for_cang4d_numbers'] = False
        context.user_data['wait_for_cang4d_cangs'] = True
        await update.message.reply_text("Nhập các càng muốn ghép (cách nhau phẩy hoặc dấu cách, ví dụ: 1 2 3):")
        return
    if context.user_data.get('wait_for_cang4d_cangs'):
        cang_list = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
        if not cang_list:
            await update.message.reply_text("Vui lòng nhập các càng (ví dụ: 1 2 3):")
            return
        numbers = context.user_data.get('cang4d_numbers', [])
        result = []
        for c in cang_list:
            for n in numbers:
                result.append(c + n)
        await update.message.reply_text(f"Kết quả ghép càng 4D ({len(result)} số):\n" + ', '.join(result))
        context.user_data['wait_for_cang4d_cangs'] = False
        context.user_data['cang4d_numbers'] = []
        await menu(update, context)
        return
    # Ghép xiên
    if isinstance(context.user_data.get('wait_for_xien_input'), int):
        text_msg = update.message.text.strip()
        numbers = split_numbers(text_msg)
        do_dai = context.user_data.get('wait_for_xien_input')
        bo_xien = ghep_xien(numbers, do_dai)
        if not bo_xien:
            await update.message.reply_text("Không ghép được xiên.")
        else:
            if len(bo_xien) > 20:
                result = '\n'.join([', '.join(bo_xien[i:i+10]) for i in range(0, len(bo_xien), 10)])
            else:
                result = ', '.join(bo_xien)
            await update.message.reply_text(f"{len(bo_xien)} bộ xiên:\n{result}")
        context.user_data['wait_for_xien_input'] = False
        await menu(update, context)
        return
    # Đảo số
    if context.user_data.get('wait_for_daoso'):
        s = update.message.text.strip()
        arr = split_numbers(s)
        s_concat = ''.join(arr) if arr else s.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (ví dụ 1234, 56789).")
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}")
        context.user_data['wait_for_daoso'] = False
        await menu(update, context)
        return
    # Góp ý/ủng hộ
    if context.user_data.get('wait_for_donggop'):
        user = update.message.from_user
        username = user.username or user.full_name or str(user.id)
        text = update.message.text.strip()
        with open("donggop_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {username} | {user.id} | {text}\n")
        await update.message.reply_text(
            "💗 Cảm ơn bạn đã gửi ủng hộ/phản hồi! Mọi phản hồi đều được ghi nhận. "
            "Bạn có thể tiếp tục sử dụng bot hoặc gửi góp ý thêm bất cứ lúc nào."
        )
        context.user_data['wait_for_donggop'] = False
        await menu(update, context)
        return
    # Chốt số theo ngày
    if context.user_data.get('wait_chot_so_ngay'):
        ngay = update.message.text.strip()
        try:
            parts = [int(x) for x in ngay.split('-')]
            if len(parts) == 3:
                y, m, d = parts
            elif len(parts) == 2:
                now = datetime.now()
                d, m = parts
                y = now.year
            else:
                raise ValueError("Sai định dạng")
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            today_str = f"{d:02d}/{m:02d}/{y}"
            text = chot_so_format(can_chi, sohap_info, today_str)
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("❗️ Nhập ngày không hợp lệ! Đúng định dạng: YYYY-MM-DD hoặc DD-MM.")
        context.user_data['wait_chot_so_ngay'] = False
        await menu(update, context)
        return
    # Phong thủy theo ngày dương
    if context.user_data.get('wait_phongthuy_ngay_duong'):
        ngay = update.message.text.strip()
        try:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if sohap_info is None:
                await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp cho ngày này!")
            else:
                text = phong_thuy_format(can_chi, sohap_info)
                await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("❗️ Nhập ngày không hợp lệ! Đúng định dạng YYYY-MM-DD.")
        context.user_data['wait_phongthuy_ngay_duong'] = False
        await menu(update, context)
        return
    # Phong thủy theo can chi
    if context.user_data.get('wait_phongthuy_ngay_canchi'):
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if sohap_info is None:
            await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp với tên bạn nhập! Kiểm tra lại định dạng (VD: Giáp Tý).")
        else:
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown")
        context.user_data['wait_phongthuy_ngay_canchi'] = False
        await menu(update, context)
        return

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

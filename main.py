import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import joblib
import subprocess
import shutil

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)
from itertools import combinations, permutations

# ==== DATA ====
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ==== CONFIG ====
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH", ".")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ==== TIỆN ÍCH ====
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
        f"{icons}\n*Chốt số hôm nay {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text

# ==== CRAWL XSMB ====
def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    table = None
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            table = tb
            break
    if not table:
        print(f"Không tìm thấy bảng kết quả {date_str}!")
        return None
    result = {"date": f"{nam}-{thang:02d}-{ngay:02d}"}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2: continue
        label = tds[0].get_text(strip=True)
        value = tds[1].get_text(" ", strip=True)
        if "Đặc biệt" in label or "ĐB" in label:
            match = re.search(r'(\d{5})(?!.*\d)', value)
            if match:
                result["DB"] = match.group(1)
            else:
                result["DB"] = value
        elif "Nhất" in label: result["G1"] = value
        elif "Nhì" in label: result["G2"] = value
        elif "Ba" in label: result["G3"] = value
        elif "Tư" in label: result["G4"] = value
        elif "Năm" in label: result["G5"] = value
        elif "Sáu" in label: result["G6"] = value
        elif "Bảy" in label: result["G7"] = value
    return result

def crawl_xsmb_15ngay_minhchinh_csv(out_csv=None):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            row = crawl_xsmb_1ngay_minhchinh_dict(date.day, date.month, date.year)
            if row:
                records.append(row)
                print(f"✔️ {date.strftime('%d-%m-%Y')} OK")
            time.sleep(1)
        except Exception as e:
            print(f"❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("date", ascending=False)
        if out_csv is None:
            out_csv = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu ngày nào!")
        return None

# ==== TRAIN MODEL RF ====
def train_rf_model_main():
    try:
        from train_rf_xsmb import train_rf_model
        csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
        train_rf_model(csv_path=csv_path, model_path=model_path)
        return True, "✅ Đã train xong, lưu rf_model_xsmb.pkl."
    except Exception as e:
        return False, f"❌ Lỗi train model: {e}"

# ==== AI DỰ ĐOÁN ====
def predict_xsmb_rf():
    model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(model_path) or not os.path.exists(csv_path):
        return "❌ Model hoặc dữ liệu xsmb.csv chưa có trên server!"
    model = joblib.load(model_path)
    df = pd.read_csv(csv_path)
    if len(df) < 3 or 'DB' not in df.columns or 'G1' not in df.columns:
        return "❌ Dữ liệu không đủ hoặc thiếu cột DB, G1"
    features = []
    for i in range(-3, 0):
        day = df.iloc[i]
        features += [int(str(day['DB'])[-2:]), int(str(day['G1'])[-2:])]
    X_pred = [features]
    y_pred = model.predict(X_pred)
    return f"🤖 Thần tài dự đoán giải đặc biệt hôm nay (2 số cuối):\n👉 {str(y_pred[0]).zfill(2)}\n(ML: Random Forest)"

# ==== THỐNG KÊ XỔ SỐ CƠ BẢN ====
def thong_ke_xsmb(n=30):
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(csv_path):
        return "❌ Chưa có file xsmb.csv trên server!"
    df = pd.read_csv(csv_path)
    df = df.sort_values("date", ascending=False)
    msg = f"📊 Thống kê {n} ngày gần nhất:\n"
    msg += "Ngày      | Đặc biệt | Giải nhất\n"
    msg += "-"*30 + "\n"
    for _, row in df.head(n).iterrows():
        msg += f"{row['date']} | {row['DB']} | {row['G1']}\n"
    return msg

# ==== BACKUP & RESTORE ====
def backup_files(to_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    os.makedirs(to_dir, exist_ok=True)
    backed = []
    for f in files:
        src = os.path.join(GITHUB_REPO_PATH, f)
        dst = os.path.join(to_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            backed.append(dst)
    return backed

def restore_files(from_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    restored = []
    for f in files:
        src = os.path.join(from_dir, f)
        dst = os.path.join(GITHUB_REPO_PATH, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            restored.append(dst)
    return restored

# ==== MENU CALLBACK ====
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
        keyboard.append([InlineKeyboardButton("🗂 Backup/Restore", callback_data="backup_restore_menu")])
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("🧠 Train & Lưu model", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬆️ Upload model lên Github", callback_data="admin_upload_model")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên Github", callback_data="admin_upload_csv")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

async def backup_restore_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📤 Backup dữ liệu", callback_data="backup_data")],
        [InlineKeyboardButton("📥 Restore dữ liệu", callback_data="restore_data")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("🗂 Backup / Restore dữ liệu:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    # --- ADMIN ---
    if query.data == "admin_menu":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu quản trị.")
            return
        await admin_menu(update, context)
        return

    # --- BACKUP/RESTORE ---
    if query.data == "backup_restore_menu":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập chức năng này.")
            return
        await backup_restore_menu(update, context)
        return
    if query.data == "backup_data":
        backed = backup_files()
        msg = "📤 Đã backup: " + ", ".join(backed)
        # Gửi file về Telegram
        for file_path in backed:
            with open(file_path, "rb") as f:
                await query.message.reply_document(document=InputFile(f))
        await query.edit_message_text(msg)
        return
    if query.data == "restore_data":
        restored = restore_files()
        msg = "📥 Đã restore: " + ", ".join(restored)
        await query.edit_message_text(msg)
        return

    # --- CRAWL, TRAIN, UPLOAD ---
    if query.data == "admin_crawl_xsmb":
        await query.edit_message_text("⏳ Đang crawl XSMB 15 ngày gần nhất, vui lòng đợi...")
        try:
            df = crawl_xsmb_15ngay_minhchinh_csv()
            if df is not None:
                await query.message.reply_document(document=open(os.path.join(GITHUB_REPO_PATH, "xsmb.csv"), "rb"), filename="xsmb.csv", caption="✅ Đã crawl xong, đây là file xsmb.csv mới nhất!")
                try:
                    os.chdir(GITHUB_REPO_PATH)
                    subprocess.run(["git", "add", "xsmb.csv"], check=True)
                    subprocess.run(["git", "commit", "-m", "update xsmb.csv (auto after crawl)"], check=True)
                    subprocess.run(["git", "push"], check=True)
                    await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
                except Exception as e:
                    await query.message.reply_text(f"❌ Lỗi upload xsmb.csv lên Github: {e}")
            else:
                await query.message.reply_text("❌ Không crawl được dữ liệu nào!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi crawl: {e}")
        return

    if query.data == "admin_train_rf":
        await query.edit_message_text("⏳ Đang train model RF...")
        ok, msg = train_rf_model_main()
        await query.message.reply_text(msg)
        if ok:
            try:
                os.chdir(GITHUB_REPO_PATH)
                subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
                subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl (auto after train)"], check=True)
                subprocess.run(["git", "push"], check=True)
                await query.message.reply_text("✅ Đã upload rf_model_xsmb.pkl lên Github!")
            except Exception as e:
                await query.message.reply_text(f"❌ Lỗi upload model lên Github: {e}")
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

    # --- DỰ ĐOÁN AI ---
    if query.data == "ml_predict":
        await query.edit_message_text("⏳ Đang dự đoán bằng AI Thần tài (Random Forest)...")
        result = predict_xsmb_rf()
        await query.message.reply_text(result)
        await menu(update, context)
        return

    # --- THỐNG KÊ ---
    if query.data == "thongke_xsmb":
        msg = thong_ke_xsmb(15)
        await query.edit_message_text(msg)
        return

    # --- GHÉP XIÊN/CÀNG/ĐẢO SỐ/PHONG THỦY/CHỐT SỐ/ỦNG HỘ... ---
    # (giữ nguyên như hướng dẫn các bản trước, không đổi)

    if query.data == "main_menu":
        await menu(update, context)
        return

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # GHÉP CÀNG 3D
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

    # GHÉP CÀNG 4D
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

    # GHÉP XIÊN
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

    # ĐẢO SỐ
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

    # CHỐT SỐ THEO NGÀY
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

    # PHONG THỦY THEO NGÀY DƯƠNG
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

    # PHONG THỦY THEO CAN CHI
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

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Bot XSMB Phong thủy AI*\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start hoặc /menu - Mở menu chính\n"
        "/help - Xem hướng dẫn\n\n"
        "Chức năng nổi bật:\n"
        "• Dự đoán AI XSMB\n"
        "• Ghép xiên, càng, đảo số\n"
        "• Tra cứu phong thủy ngày\n"
        "• Chốt số, hỗ trợ nhiều chế độ\n"
        "• Thống kê, quản trị, backup, cập nhật model\n"
        "• Nhận góp ý, phản hồi, ủng hộ bot"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚨 Exception:\n{context.error}"
            )
        except Exception:
            pass

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.add_error_handler(error_handler)
    logger.info("🤖 BOT XSMB đã chạy thành công!")
    app.run_polling()

if __name__ == "__main__":
    main()

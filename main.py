import os
import logging
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
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
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ============= CRAWL XSMB ============
def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
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
        elif "Nhất" in label:
            result["G1"] = value
        elif "Nhì" in label:
            result["G2"] = value
        elif "Ba" in label:
            result["G3"] = value
        elif "Tư" in label:
            result["G4"] = value
        elif "Năm" in label:
            result["G5"] = value
        elif "Sáu" in label:
            result["G6"] = value
        elif "Bảy" in label:
            result["G7"] = value
    return result

def crawl_xsmb_15ngay_minhchinh_csv(out_csv="xsmb.csv"):
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
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu ngày nào!")
        return None

# ============= CRAWL XSMN =============
def crawl_xsmn_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-nam/{date_str}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    result_list = []
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            province_cells = trs[0].find_all("td")
            province_names = [td.get_text(strip=True) for td in province_cells[1:]] if len(province_cells) > 1 else []
            if not province_names:
                continue
            province_data = {name: {"date": f"{nam}-{thang:02d}-{ngay:02d}", "province": name} for name in province_names}
            for tr in trs[1:]:
                tds = tr.find_all("td")
                if len(tds) != len(province_names) + 1:
                    continue
                label = tds[0].get_text(strip=True)
                for i, name in enumerate(province_names):
                    value = tds[i+1].get_text(" ", strip=True)
                    if "Đặc biệt" in label or "ĐB" in label:
                        province_data[name]["DB"] = value
                    elif "Nhất" in label:
                        province_data[name]["G1"] = value
                    elif "Nhì" in label:
                        province_data[name]["G2"] = value
                    elif "Ba" in label:
                        province_data[name]["G3"] = value
                    elif "Tư" in label:
                        province_data[name]["G4"] = value
                    elif "Năm" in label:
                        province_data[name]["G5"] = value
                    elif "Sáu" in label:
                        province_data[name]["G6"] = value
                    elif "Bảy" in label:
                        province_data[name]["G7"] = value
            result_list += list(province_data.values())
    return result_list

def crawl_xsmn_15ngay_minhchinh_csv(out_csv="xsmn.csv"):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            day_records = crawl_xsmn_1ngay_minhchinh_dict(date.day, date.month, date.year)
            if day_records:
                records.extend(day_records)
                print(f"✔️ {date.strftime('%d-%m-%Y')} OK ({len(day_records)} tỉnh)")
            time.sleep(1)
        except Exception as e:
            print(f"❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values(["date", "province"], ascending=[False, True])
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày XSMN vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu miền Nam ngày nào!")
        return None

# ============= CRAWL XSMT =============
def crawl_xsmt_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-trung/{date_str}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    result_list = []
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            province_cells = trs[0].find_all("td")
            province_names = [td.get_text(strip=True) for td in province_cells[1:]] if len(province_cells) > 1 else []
            if not province_names:
                continue
            province_data = {name: {"date": f"{nam}-{thang:02d}-{ngay:02d}", "province": name} for name in province_names}
            for tr in trs[1:]:
                tds = tr.find_all("td")
                if len(tds) != len(province_names) + 1:
                    continue
                label = tds[0].get_text(strip=True)
                for i, name in enumerate(province_names):
                    value = tds[i+1].get_text(" ", strip=True)
                    if "Đặc biệt" in label or "ĐB" in label:
                        province_data[name]["DB"] = value
                    elif "Nhất" in label:
                        province_data[name]["G1"] = value
                    elif "Nhì" in label:
                        province_data[name]["G2"] = value
                    elif "Ba" in label:
                        province_data[name]["G3"] = value
                    elif "Tư" in label:
                        province_data[name]["G4"] = value
                    elif "Năm" in label:
                        province_data[name]["G5"] = value
                    elif "Sáu" in label:
                        province_data[name]["G6"] = value
                    elif "Bảy" in label:
                        province_data[name]["G7"] = value
            result_list += list(province_data.values())
    return result_list

def crawl_xsmt_15ngay_minhchinh_csv(out_csv="xsmt.csv"):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            day_records = crawl_xsmt_1ngay_minhchinh_dict(date.day, date.month, date.year)
            if day_records:
                records.extend(day_records)
                print(f"✔️ {date.strftime('%d-%m-%Y')} OK ({len(day_records)} tỉnh)")
            time.sleep(1)
        except Exception as e:
            print(f"❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values(["date", "province"], ascending=[False, True])
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày XSMT vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu miền Trung ngày nào!")
        return None

# ===== TIỆN ÍCH: split_numbers, ghep_xien, dao_so, các hàm phong thủy... giữ nguyên như bản mở rộng trước!
# ===== PHẦN 2: CALLBACK MENU & HANDLER NHẬP LIỆU =====

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = (
        update.effective_user.id
        if update.effective_user
        else (update.message.from_user.id if update.message else None)
    )
    keyboard = [
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])

    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("📥 Crawl XSMN", callback_data="admin_crawl_xsmn")],
        [InlineKeyboardButton("📥 Crawl XSMT", callback_data="admin_crawl_xsmt")],
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

    # === MENU ADMIN - 3 MIỀN ===
    if query.data == "admin_menu":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu quản trị.")
            return
        await admin_menu(update, context)
        return

    if query.data == "admin_crawl_xsmb":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này.")
            return
        await query.edit_message_text("⏳ Đang crawl kết quả XSMB 15 ngày gần nhất, vui lòng đợi...")
        try:
            df = crawl_xsmb_15ngay_minhchinh_csv("xsmb.csv")
            if df is not None:
                file_path = "xsmb.csv"
                await query.message.reply_document(document=open(file_path, "rb"), filename="xsmb.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMB 15 ngày gần nhất!")
            else:
                await query.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
                sys.exit(1)
        except Exception as e:
            await query.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
            sys.exit(1)
        return

    if query.data == "admin_crawl_xsmn":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này.")
            return
        await query.edit_message_text("⏳ Đang crawl kết quả XSMN 15 ngày gần nhất, vui lòng đợi...")
        try:
            df = crawl_xsmn_15ngay_minhchinh_csv("xsmn.csv")
            if df is not None:
                file_path = "xsmn.csv"
                await query.message.reply_document(document=open(file_path, "rb"), filename="xsmn.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMN 15 ngày gần nhất!")
            else:
                await query.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
                sys.exit(1)
        except Exception as e:
            await query.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
            sys.exit(1)
        return

    if query.data == "admin_crawl_xsmt":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này.")
            return
        await query.edit_message_text("⏳ Đang crawl kết quả XSMT 15 ngày gần nhất, vui lòng đợi...")
        try:
            df = crawl_xsmt_15ngay_minhchinh_csv("xsmt.csv")
            if df is not None:
                file_path = "xsmt.csv"
                await query.message.reply_document(document=open(file_path, "rb"), filename="xsmt.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMT 15 ngày gần nhất!")
            else:
                await query.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
                sys.exit(1)
        except Exception as e:
            await query.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
            sys.exit(1)
        return

    # ==== GHÉP XIÊN ====
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

    # ==== GHÉP CÀNG/ĐẢO SỐ ====
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

    # ==== PHONG THỦY ====
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

    # ==== CHỐT SỐ ====
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

    # ==== GÓP Ý ====
    if query.data == "donggop":
        keyboard = [
            [InlineKeyboardButton("Gửi góp ý", callback_data="donggop_gui")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("💗 Hãy gửi góp ý/ủng hộ bot!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "donggop_gui":
        context.user_data.clear()
        context.user_data['wait_for_donggop'] = True
        await query.edit_message_text("🙏 Vui lòng nhập góp ý, phản hồi hoặc lời nhắn của bạn (mọi góp ý đều được ghi nhận và tri ân công khai).")
        return

    if query.data == "main_menu":
        await menu(update, context)
        return

    await menu(update, context)

# ===== PHẦN 3: HANDLER NHẬP LIỆU + MAIN =====

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ==== Ghép càng 3D ====
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

    # ==== Ghép càng 4D ====
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

    # ==== Ghép xiên ====
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

    # ==== Đảo số ====
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

    # ==== Góp ý ====
    if context.user_data.get('wait_for_donggop'):
        user = update.message.from_user
        username = user.username or user.full_name or str(user.id)
        text = update.message.text.strip()
        with open("donggop_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {username} | {user.id} | {text}\n")
        await update.message.reply_text(
            "💗 Cảm ơn bạn đã gửi góp ý/ủng hộ! Tất cả phản hồi đều được trân trọng ghi nhận.\n"
            "Bạn có thể tiếp tục sử dụng bot hoặc gửi góp ý thêm bất cứ lúc nào."
        )
        context.user_data['wait_for_donggop'] = False
        await menu(update, context)
        return

    # ==== Chốt số theo ngày ====
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

    # ==== Phong thủy theo ngày dương ====
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

    # ==== Phong thủy theo can chi ====
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

    await update.message.reply_text("Bot đã nhận tin nhắn của bạn! Vui lòng chọn chức năng từ menu.")
    await menu(update, context)

# ===== CÁC LỆNH CRAWL NHANH (admin dùng) =====
async def crawl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
        return
    await update.message.reply_text("⏳ Đang crawl kết quả XSMB 15 ngày gần nhất...")
    try:
        df = crawl_xsmb_15ngay_minhchinh_csv("xsmb.csv")
        if df is not None:
            file_path = "xsmb.csv"
            await update.message.reply_document(document=open(file_path, "rb"), filename="xsmb.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMB 15 ngày gần nhất!")
        else:
            await update.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
            sys.exit(1)
    except Exception as e:
        await update.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
        sys.exit(1)

async def crawlmn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
        return
    await update.message.reply_text("⏳ Đang crawl kết quả XSMN 15 ngày gần nhất...")
    try:
        df = crawl_xsmn_15ngay_minhchinh_csv("xsmn.csv")
        if df is not None:
            file_path = "xsmn.csv"
            await update.message.reply_document(document=open(file_path, "rb"), filename="xsmn.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMN 15 ngày gần nhất!")
        else:
            await update.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
            sys.exit(1)
    except Exception as e:
        await update.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
        sys.exit(1)

async def crawlt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
        return
    await update.message.reply_text("⏳ Đang crawl kết quả XSMT 15 ngày gần nhất...")
    try:
        df = crawl_xsmt_15ngay_minhchinh_csv("xsmt.csv")
        if df is not None:
            file_path = "xsmt.csv"
            await update.message.reply_document(document=open(file_path, "rb"), filename="xsmt.csv", caption="✅ Đã crawl xong, đây là file kết quả XSMT 15 ngày gần nhất!")
        else:
            await update.message.reply_text("❌ Không crawl được dữ liệu nào. Dừng bot.")
            sys.exit(1)
    except Exception as e:
        await update.message.reply_text(f"❗ Lỗi khi crawl: {e}\nBot sẽ dừng lại.")
        sys.exit(1)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("crawl", crawl_handler))
    app.add_handler(CommandHandler("crawlmn", crawlmn_handler))
    app.add_handler(CommandHandler("crawlt", crawlt_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()


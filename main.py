import os
import logging
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

# ============= PHÂN QUYỀN ADMIN ============
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

# ============= TIỆN ÍCH PHONG THỦY, XIÊN, CHỐT SỐ ============
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
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
    if not code:
        return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j:
                ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can,
        "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"),
        "so_menh": so_menh,
        "so_hap_list": so_ghep,
        "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")

    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else:
        so_hap_can = "?"
        so_menh = "?"

    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"

    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"

    text = (
        f"{main_line}\n"
        f"- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n"
        f"- Số hạp ngày: {so_hap_ngay}"
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
            if x != y:
                lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n"
        f"*Chốt số 3 miền ngày {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\n"
        f"Lô: {', '.join(lo)}"
    )
    return text

# ========== MENU & CALLBACK ==========
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
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

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
            await update.message.reply_text("❌ Không crawl được dữ liệu nào.")
    except Exception as e:
        await update.message.reply_text(f"❗ Lỗi khi crawl: {e}")

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # ... các callback menu khác của bạn ở đây ...

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
                await query.message.reply_text("❌ Không crawl được dữ liệu nào.")
        except Exception as e:
            await query.message.reply_text(f"❗ Lỗi khi crawl: {e}")
        return

    # ... các callback menu khác giữ nguyên theo code của bạn ...

# ========== ALL TEXT HANDLER ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Nếu không có context đặc biệt, mặc định trả về menu
    await update.message.reply_text("Bot đã nhận tin nhắn của bạn! Vui lòng chọn chức năng từ menu.")
    await menu(update, context)

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("crawl", crawl_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

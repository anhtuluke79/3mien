import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# ================= CRAWL XỔ SỐ 3 MIỀN ================

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

def crawl_xsmn_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-nam/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    result_list = []
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            province_cells = trs[0].find_all("td")
            province_names = [td.get_text(strip=True) for td in province_cells[1:]] if len(province_cells) > 1 else []
            if not province_names: continue
            province_data = {name: {"date": f"{nam}-{thang:02d}-{ngay:02d}", "province": name} for name in province_names}
            for tr in trs[1:]:
                tds = tr.find_all("td")
                if len(tds) != len(province_names) + 1: continue
                label = tds[0].get_text(strip=True)
                for i, name in enumerate(province_names):
                    value = tds[i+1].get_text(" ", strip=True)
                    if "Đặc biệt" in label or "ĐB" in label: province_data[name]["DB"] = value
                    elif "Nhất" in label: province_data[name]["G1"] = value
                    elif "Nhì" in label: province_data[name]["G2"] = value
                    elif "Ba" in label: province_data[name]["G3"] = value
                    elif "Tư" in label: province_data[name]["G4"] = value
                    elif "Năm" in label: province_data[name]["G5"] = value
                    elif "Sáu" in label: province_data[name]["G6"] = value
                    elif "Bảy" in label: province_data[name]["G7"] = value
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

def crawl_xsmt_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-trung/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    result_list = []
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            province_cells = trs[0].find_all("td")
            province_names = [td.get_text(strip=True) for td in province_cells[1:]] if len(province_cells) > 1 else []
            if not province_names: continue
            province_data = {name: {"date": f"{nam}-{thang:02d}-{ngay:02d}", "province": name} for name in province_names}
            for tr in trs[1:]:
                tds = tr.find_all("td")
                if len(tds) != len(province_names) + 1: continue
                label = tds[0].get_text(strip=True)
                for i, name in enumerate(province_names):
                    value = tds[i+1].get_text(" ", strip=True)
                    if "Đặc biệt" in label or "ĐB" in label: province_data[name]["DB"] = value
                    elif "Nhất" in label: province_data[name]["G1"] = value
                    elif "Nhì" in label: province_data[name]["G2"] = value
                    elif "Ba" in label: province_data[name]["G3"] = value
                    elif "Tư" in label: province_data[name]["G4"] = value
                    elif "Năm" in label: province_data[name]["G5"] = value
                    elif "Sáu" in label: province_data[name]["G6"] = value
                    elif "Bảy" in label: province_data[name]["G7"] = value
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

# ================= TIỆN ÍCH =================
# (Các hàm: split_numbers, ghep_xien, dao_so, chuan_hoa_can_chi, get_can_chi_ngay,
# sinh_so_hap_cho_ngay, phong_thuy_format, chot_so_format
# Giữ nguyên như các bản ở trên, không rút gọn, đều OK.)

# ================= MENU, CALLBACK, HANDLER, MAIN =================
# --- Bạn copy TOÀN BỘ các hàm menu, admin_menu, menu_callback_handler, all_text_handler ở các phần trên vào đây ---
# --- Ở trên, mình đã gửi đầy đủ và bạn chỉ cần dán lại liên tục các khối menu + handler (tách biệt với các hàm crawl) ---

# ========== CÁC LỆNH CRAWL PHẢI NẰM NGOÀI MAIN ==========
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

# ========== MAIN ==========
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

import os

# --- GHI FILE service_account.json từ biến môi trường ---
if not os.path.exists('service_account.json'):
    json_content = os.getenv("GDRIVE_JSON")
    if json_content:
        import json
        try:
            obj = json.loads(json_content)
            with open('service_account.json', 'w') as f:
                json.dump(obj, f)
        except Exception:
            with open('service_account.json', 'w') as f:
                f.write(json_content)

import logging
import pandas as pd
import joblib
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)
from itertools import product, combinations
import datetime
import re
from collections import Counter
import asyncio

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

from gdrive_helper import upload_file_to_gdrive, download_file_from_gdrive

DATA_FILE = '/tmp/xsmb_full.csv'
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- TẢI CSV TỪ GOOGLE DRIVE KHI KHỞI ĐỘNG ---
if not os.path.exists(DATA_FILE):
    try:
        download_file_from_gdrive("xsmb_full.csv", DATA_FILE)
        print("Đã tải dữ liệu từ Google Drive.")
    except Exception as e:
        print("Không tìm thấy file trên Drive, sẽ tạo mới sau.", e)

def ask_gemini(prompt, api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Bạn chưa cấu hình GEMINI_API_KEY!"
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(f"{url}?key={api_key}", json=data, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Gemini API lỗi: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Lỗi gọi Gemini API: {str(e)}"

def split_numbers(s):
    return re.findall(r'\d+', s)

def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0:
        return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

def get_can_chi_ngay(year, month, day):
    if month < 3:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    chi = chi_list[(jd + 1) % 12]
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    can = can_list[(jd + 9) % 10]
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

def crawl_xsmb_one_day(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="table-kq-xsmb")
    if not table:
        return None
    caption = table.find("caption")
    date_text = caption.get_text(strip=True) if caption else "Không rõ ngày"
    match = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
    date = match.group(1) if match else date_text
    result = {"Ngày": date}
    rows = table.find_all("tr")
    for row in rows:
        th = row.find("th")
        if th:
            ten_giai = th.get_text(strip=True)
            numbers = [td.get_text(strip=True) for td in row.find_all("td")]
            result[ten_giai] = ", ".join(numbers)
    return result

def get_latest_date_in_csv(filename):
    if not os.path.exists(filename):
        return None
    df = pd.read_csv(filename, encoding="utf-8-sig")
    df = df.dropna(subset=["Ngày"])
    df["Ngày_sort"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    latest = df["Ngày_sort"].max()
    return latest

async def crawl_new_days_csv_progress(query, filename=DATA_FILE, max_pages=60):
    await query.edit_message_text("⏳ Bắt đầu cập nhật dữ liệu xsmb_full.csv (60 ngày)...")
    latest_date = get_latest_date_in_csv(filename)
    base_url = "https://xoso.com.vn/xo-so-mien-bac/xsmb-p{}.html"
    new_results = []
    for i in range(1, max_pages + 1):
        url = base_url.format(i)
        kq = crawl_xsmb_one_day(url)
        if kq is None:
            await query.edit_message_text(
                f"✅ Đã crawl xong {len(new_results)} ngày mới. Hoàn thành cập nhật (không còn trang dữ liệu)."
            )
            break
        try:
            date_obj = datetime.datetime.strptime(kq["Ngày"], "%d/%m/%Y")
        except:
            await query.edit_message_text(
                f"Lỗi định dạng ngày: {kq['Ngày']} tại trang {url}. Dừng cập nhật.")
            return False
        if latest_date and date_obj <= latest_date:
            await query.edit_message_text(
                f"✅ Đã crawl xong {len(new_results)} ngày mới. Hoàn thành cập nhật."
            )
            break
        new_results.append(kq)
        if i % 3 == 0 or i == 1:
            await query.edit_message_text(
                f"⏳ Đang crawl trang {i}/{max_pages}...\n"
                f"Đã lấy được ngày: {', '.join([x['Ngày'] for x in new_results[-3:]])}"
            )
        await asyncio.sleep(0.5)
    if not new_results:
        await query.edit_message_text("Không có dữ liệu mới cần cập nhật.")
        return False
    df_new = pd.DataFrame(new_results)
    if os.path.exists(filename):
        df_old = pd.read_csv(filename, encoding="utf-8-sig")
        df_full = pd.concat([df_new, df_old], ignore_index=True)
        df_full = df_full.drop_duplicates(subset=["Ngày"], keep="first")
    else:
        df_full = df_new
    df_full["Ngày_sort"] = pd.to_datetime(df_full["Ngày"], format="%d/%m/%Y", errors="coerce")
    df_full = df_full.sort_values("Ngày_sort", ascending=False).drop("Ngày_sort", axis=1)
    df_full.to_csv(filename, index=False, encoding="utf-8-sig")
    # --- UPLOAD file lên Google Drive ---
    try:
        upload_file_to_gdrive(filename)
    except Exception as e:
        print("Upload Google Drive lỗi:", e)
    await query.edit_message_text(
        f"✅ Đã cập nhật {len(new_results)} ngày mới vào xsmb_full.csv thành công!"
    )
    return True

# ...Các hàm, handler, flow menu, context, bảo vệ context, các lệnh /menu, ghép xiên, ghép càng, phong thủy, train AI, download csv... (giữ đúng như bản bạn đã test kỹ ở trên) ...

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), all_text_handler))
    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
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

DATA_FILE = '/tmp/xsmb_full.csv'
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.path.exists(DATA_FILE):
    try:
        download_file_from_gdrive("xsmb_full.csv", DATA_FILE)
        print("Đã tải dữ liệu từ Google Drive.")
    except Exception as e:
        print("Không tìm thấy file trên Drive, sẽ tạo mới sau.", e)

def split_numbers(s):
    return [num.lstrip('0') if num != '00' else '00' for num in re.findall(r'\d+', str(s)) if len(num) <= 4]

def ghep_xien(numbers, do_dai=2):
    numbers = [str(n).zfill(2) for n in numbers]
    if len(numbers) < do_dai:
        return []
    return [('&'.join(comb)) for comb in combinations(numbers, do_dai)]

def ghep_cang(cang_list, so_list):
    result = []
    for c in cang_list:
        for so in so_list:
            result.append(f"{c}{so}")
    return result

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
    try:
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
        for row in table.find_all("tr"):
            th = row.find("th")
            if th:
                ten_giai = th.get_text(strip=True)
                numbers = [td.get_text(strip=True) for td in row.find_all("td")]
                result[ten_giai] = ", ".join(numbers)
        if all(k in result for k in ['Đặc biệt', 'Giải nhất', 'Giải nhì']):
            return result
        return None
    except Exception as ex:
        logger.warning(f"Lỗi crawl {url}: {ex}")
        return None

def get_latest_date_in_csv(filename):
    if not os.path.exists(filename):
        return None
    df = pd.read_csv(filename, encoding="utf-8-sig")
    df = df.dropna(subset=["Ngày"])
    df["Ngày_sort"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    latest = df["Ngày_sort"].max()
    return latest

async def crawl_new_days_csv_progress(query, filename=DATA_FILE, max_pages=60):
    await query.edit_message_text("⏳ Đang cập nhật dữ liệu xsmb_full.csv...")
    latest_date = get_latest_date_in_csv(filename)
    base_url = "https://xoso.com.vn/xo-so-mien-bac/xsmb-p{}.html"
    new_results = []
    for i in range(1, max_pages + 1):
        url = base_url.format(i)
        kq = crawl_xsmb_one_day(url)
        if kq is None:
            if i == 1:
                await query.edit_message_text("❌ Không lấy được dữ liệu từ nguồn. Có thể web bị chặn hoặc thay đổi giao diện.")
                return False
            break
        try:
            date_obj = datetime.datetime.strptime(kq["Ngày"], "%d/%m/%Y")
        except Exception as ex:
            await query.edit_message_text(f"Lỗi định dạng ngày {kq['Ngày']} tại trang {url}: {ex}")
            return False
        if latest_date and date_obj <= latest_date:
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
    try:
        upload_file_to_gdrive(filename)
    except Exception as e:
        logger.warning(f"Upload Google Drive lỗi: {e}")
    await query.edit_message_text(
        f"✅ Đã cập nhật {len(new_results)} ngày mới vào xsmb_full.csv thành công!"
    )
    return True

def thong_ke_lo(csv_file=DATA_FILE, days=7):
    if not os.path.exists(csv_file):
        return [], []
    df = pd.read_csv(csv_file)
    df = df.head(days)
    all_lo = []
    for _, row in df.iterrows():
        for col in df.columns:
            if col != 'Ngày' and pd.notnull(row[col]):
                nums = [n.strip() for n in str(row[col]).split(',')]
                all_lo.extend([n[-2:] for n in nums if n[-2:].isdigit()])
    lo_counter = Counter(all_lo)
    top_lo = lo_counter.most_common(10)
    total_lo = sum(lo_counter.values()) if lo_counter else 1
    xac_suat = [(l, c, round(c/total_lo*100,1)) for l,c in top_lo]
    tat_ca_lo = {f"{i:02d}" for i in range(100)}
    da_ve = set(lo_counter.keys())
    lo_gan = list(tat_ca_lo - da_ve)
    return xac_suat, lo_gan

async def send_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này!")
        return
    if not os.path.exists(DATA_FILE):
        await update.message.reply_text("Chưa có file dữ liệu.")
        return
    await update.message.reply_document(InputFile(DATA_FILE), filename="xsmb_full.csv")

async def send_csv_callback(query, user_id):
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("Bạn không có quyền sử dụng chức năng này!")
        return
    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("Chưa có file dữ liệu.")
        return
    await query.message.reply_document(InputFile(DATA_FILE), filename="xsmb_full.csv")
    await query.edit_message_text("⬇️ File xsmb_full.csv đã được gửi.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🧠 Dự đoán AI", callback_data="du_doan_ai"),
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("💬 Hỏi Thần tài", callback_data="hoi_gemini"),
        ],
        [
            InlineKeyboardButton("🤖 AI cầu lô", callback_data="ai_lo_menu"),
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("⚙️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
            InlineKeyboardButton("⬇️ Download CSV", callback_data="download_csv"),
            InlineKeyboardButton("⚙️ Train lại AI", callback_data="train_model"),
        ])
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "download_csv":
        await send_csv_callback(query, user_id)
        return

    if query.data == "ghepcang":
        context.user_data["wait_cang_step"] = "cang"
        await query.edit_message_text("Nhập dãy càng muốn ghép (ví dụ: 1 2 3):")
        return

    if query.data == "ghepxien":
        keyboard = [
            [
                InlineKeyboardButton("Xiên 2", callback_data="ghepxien2"),
                InlineKeyboardButton("Xiên 3", callback_data="ghepxien3"),
                InlineKeyboardButton("Xiên 4", callback_data="ghepxien4"),
            ]
        ]
        await query.edit_message_text(
            "Chọn loại ghép xiên:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data in ["ghepxien2", "ghepxien3", "ghepxien4"]:
        xiend = int(query.data[-1])
        await query.edit_message_text(f"Nhập dãy số (cách nhau bởi dấu cách, phẩy) để ghép xiên {xiend}:")
        context.user_data["wait_xien"] = True
        context.user_data["who_xien"] = user_id
        context.user_data["xiend"] = xiend
        return

    # ... các phần callback khác như cũ, không đổi (AI, train_model, thống kê, v.v.)

    # (Không đưa lại full vì quá dài, nếu cần mình gửi lại toàn bộ các lệnh admin/stat/ai...)

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # === LUỒNG GHÉP CÀNG 2 BƯỚC ===
    if context.user_data.get("wait_cang_step") == "cang":
        cang_list = re.findall(r'\d+', text)
        if not cang_list:
            await update.message.reply_text("Hãy nhập dãy càng (cách nhau bằng dấu phẩy hoặc dấu cách, ví dụ: 1 2 3)")
            return
        context.user_data["cang_list"] = cang_list
        context.user_data["wait_cang_step"] = "so"
        await update.message.reply_text("Nhập dãy số cần ghép (ví dụ: 23 75 46 96):")
        return

    if context.user_data.get("wait_cang_step") == "so":
        so_list = re.findall(r'\d+', text)
        cang_list = context.user_data.get("cang_list", [])
        if not so_list or not cang_list:
            await update.message.reply_text("Thiếu càng hoặc số. Vui lòng nhập lại.")
        else:
            result = ghep_cang(cang_list, so_list)
            MAX_SHOW = 50
            preview = ','.join(result[:MAX_SHOW])
            tail = " ..." if len(result) > MAX_SHOW else ""
            await update.message.reply_text(f"Kết quả ghép càng: {preview}{tail}")
        context.user_data["wait_cang_step"] = None
        context.user_data["cang_list"] = None
        return

    # === LUỒNG GHÉP XIÊN ===
    if context.user_data.get("wait_xien", False):
        if context.user_data.get("who_xien", None) == user_id:
            xiend = context.user_data.get("xiend", 2)
            nums = split_numbers(text)
            if len(nums) < xiend:
                await update.message.reply_text(f"Cần nhập tối thiểu {xiend} số để ghép xiên. Vui lòng gửi lại.")
            else:
                xiens = ghep_xien(nums, xiend)
                MAX_SHOW = 50
                preview = ', '.join(xiens[:MAX_SHOW])
                tail = " ..." if len(xiens) > MAX_SHOW else ""
                await update.message.reply_text(f"Các bộ xiên {xiend}: {preview}{tail}")
            context.user_data["wait_xien"] = False
            context.user_data["who_xien"] = None
            context.user_data["xiend"] = None
        return

    # === HỎI GEMINI ===
    if context.user_data.get("wait_gemini", False):
        if context.user_data.get("who_gemini", None) == user_id:
            res = ask_gemini(text)
            await update.message.reply_text(f"💬 Thần tài trả lời:\n{res}")
            context.user_data["wait_gemini"] = False
            context.user_data["who_gemini"] = None
        return

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("download_csv", send_csv))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), all_text_handler))
    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

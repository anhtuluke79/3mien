import os
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)
from itertools import combinations, permutations
import datetime
import re
import asyncio

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO
from gdrive_helper import upload_file_to_gdrive, download_file_from_gdrive

DATA_FILE = '/tmp/xsmb_full.csv'
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def ghep_cang(cang_list, so_list):
    res = []
    for cang in cang_list:
        for so in so_list:
            res.append(str(cang) + str(so))
    return sorted(set(res))

def sinh_lat_so(s):
    return [ ''.join(p) for p in sorted(set(permutations(s)))]

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

def crawl_xsmb_one_day_ketqua04(day_obj):
    url = f"https://ketqua04.net/xo-so-truyen-thong.php?ngay={day_obj.strftime('%d-%m-%Y')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="kqmienbac")
    if not table:
        return None
    result = {"Ngày": day_obj.strftime("%d/%m/%Y")}
    rows = table.find_all("tr")
    for row in rows:
        th = row.find("th")
        if th:
            ten_giai = th.text.strip()
            numbers = [td.get_text(strip=True) for td in row.find_all("td")]
            if numbers:
                result[ten_giai] = ', '.join(numbers)
    name_map = {
        "ĐB": "Đặc biệt", "G1": "Giải nhất", "G2": "Giải nhì", "G3": "Giải ba",
        "G4": "Giải tư", "G5": "Giải năm", "G6": "Giải sáu", "G7": "Giải bảy"
    }
    for src, dst in name_map.items():
        if src in result:
            result[dst] = result.pop(src)
    return result if "Đặc biệt" in result and "Giải nhất" in result else None

def get_latest_date_in_csv(filename):
    if not os.path.exists(filename):
        return None
    df = pd.read_csv(filename, encoding="utf-8-sig")
    df = df.dropna(subset=["Ngày"])
    df["Ngày_sort"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    latest = df["Ngày_sort"].max()
    return latest

async def crawl_new_days_csv_progress(query, filename=DATA_FILE, max_days=60):
    await query.edit_message_text("⏳ Đang cập nhật dữ liệu xsmb_full.csv (nguồn ketqua04.net)...")
    latest_date = get_latest_date_in_csv(filename)
    today = datetime.date.today()
    new_results = []
    for i in range(max_days):
        day = today - datetime.timedelta(days=i)
        if latest_date and day <= latest_date.date():
            break
        kq = crawl_xsmb_one_day_ketqua04(day)
        if kq is None:
            continue
        new_results.append(kq)
        if (i+1) % 3 == 0 or i == 0:
            await query.edit_message_text(
                f"⏳ Đang crawl ngày {day.strftime('%d/%m/%Y')} ({i+1}/{max_days})...\n"
                f"Đã lấy: {', '.join([x['Ngày'] for x in new_results[-3:]])}"
            )
        await asyncio.sleep(0.5)
    if not new_results:
        await query.edit_message_text("Không có dữ liệu mới cần cập nhật (nguồn ketqua04.net).")
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
        f"✅ Đã cập nhật {len(new_results)} ngày mới vào xsmb_full.csv thành công! (nguồn ketqua04.net)"
    )
    return True

async def send_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này!")
        return
    if not os.path.exists(DATA_FILE):
        await update.message.reply_text("Chưa có file dữ liệu. Hãy cập nhật XSMB trước.")
        return
    await update.message.reply_document(InputFile(DATA_FILE), filename="xsmb_full.csv")

async def send_csv_callback(query, user_id):
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("Bạn không có quyền sử dụng chức năng này!")
        return
    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("Chưa có file dữ liệu. Hãy cập nhật XSMB trước.")
        return
    await query.message.reply_document(InputFile(DATA_FILE), filename="xsmb_full.csv")
    await query.edit_message_text("⬇️ File xsmb_full.csv đã được gửi.")

# ============ HANDLER CALLBACK/COMMAND ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wait_gemini"] = False
    context.user_data["who_gemini"] = None
    context.user_data["gemini_count"] = 0
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wait_gemini"] = False
    context.user_data["who_gemini"] = None
    context.user_data["gemini_count"] = 0
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
            InlineKeyboardButton("💬 Thần tài tư vấn", callback_data="hoi_gemini"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 3D/4D/Đảo số", callback_data="ghepcang"),
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("⚙️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
            InlineKeyboardButton("⬇️ Download CSV", callback_data="download_csv"),
        ])
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Reset trạng thái Gemini khi đổi menu
    context.user_data["wait_gemini"] = False
    context.user_data["who_gemini"] = None
    context.user_data["gemini_count"] = 0

    if query.data == "download_csv":
        await send_csv_callback(query, user_id)
        return

    if query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await crawl_new_days_csv_progress(query, DATA_FILE, 60)
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

    if query.data == "ghepcang":
        keyboard = [
            [
                InlineKeyboardButton("3D", callback_data="ghepcang3"),
                InlineKeyboardButton("4D", callback_data="ghepcang4"),
                InlineKeyboardButton("Đảo/Lật số", callback_data="latso")
            ]
        ]
        await query.edit_message_text(
            "Chọn loại 3D, 4D hoặc đảo số:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    if query.data in ["ghepcang3", "ghepcang4"]:
        socang = int(query.data[-1])
        await query.edit_message_text(f"Nhập dãy càng muốn ghép (ví dụ: 1 2 3):")
        context.user_data["wait_cang"] = True
        context.user_data["who_cang"] = user_id
        context.user_data["socang"] = socang
        context.user_data["stage"] = "nhap_cang"
        return
    if query.data == "latso":
        context.user_data["wait_latso"] = True
        await query.edit_message_text("Nhập số 3 hoặc 4 chữ số để đảo/lật (ví dụ: 123 hoặc 1234):")
        return

    if query.data == "phongthuy_ngay":
        now = datetime.datetime.now()
        can_chi = get_can_chi_ngay(now.year, now.month, now.day)
        so_hap = sinh_so_hap_cho_ngay(can_chi)
        if so_hap:
            msg = (
                f"🔮 Phong thủy ngày {now.strftime('%d/%m/%Y')}\n"
                f"Can Chi: {can_chi}\n"
                f"Số mệnh: {so_hap['so_menh']}\n"
                f"Số hợp: {', '.join(so_hap['so_hap_list'])}\n"
                f"Đề xuất các cặp số hợp: {', '.join(so_hap['so_ghép'])}"
            )
        else:
            msg = f"Không tra được phong thủy cho ngày {now.strftime('%d/%m/%Y')}"
        await query.edit_message_text(msg)
        return

    if query.data == "hoi_gemini":
        context.user_data["wait_gemini"] = True
        context.user_data["who_gemini"] = user_id
        context.user_data["gemini_count"] = 0
        await query.edit_message_text("Nhập nội dung bạn muốn hỏi Thần tài tư vấn. Bạn có 10 lượt hỏi trong phiên này:")
        return

    await query.edit_message_text("Chức năng này đang phát triển hoặc chưa được cấu hình!")

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

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
                await update.message.reply_text(f"{preview}{tail}")
            context.user_data["wait_xien"] = False
            context.user_data["who_xien"] = None
            context.user_data["xiend"] = None
        return

    if context.user_data.get("wait_cang", False):
        if context.user_data.get("who_cang", None) == user_id:
            stage = context.user_data.get("stage", "")
            if stage == "nhap_cang":
                cang_list = split_numbers(text)
                if not cang_list:
                    await update.message.reply_text("Bạn phải nhập ít nhất 1 càng!")
                    return
                context.user_data["cang_list"] = cang_list
                context.user_data["stage"] = "nhap_so"
                socang = context.user_data["socang"]
                if socang == 3:
                    await update.message.reply_text("Nhập dãy số 2 chữ số cần ghép càng (cách nhau bởi dấu cách, phẩy):")
                else:
                    await update.message.reply_text("Nhập dãy số 3 chữ số cần ghép càng (cách nhau bởi dấu cách, phẩy):")
                return
            elif stage == "nhap_so":
                so_list = split_numbers(text)
                cang_list = context.user_data.get("cang_list", [])
                socang = context.user_data.get("socang", 3)
                if socang == 3:
                    so_list = [s for s in so_list if len(s) == 2]
                else:
                    so_list = [s for s in so_list if len(s) == 3]
                if not so_list:
                    await update.message.reply_text(f"Phải nhập số {'2' if socang==3 else '3'} chữ số!")
                else:
                    cangs = ghep_cang(cang_list, so_list)
                    MAX_SHOW = 50
                    preview = ','.join(cangs[:MAX_SHOW])
                    tail = " ..." if len(cangs) > MAX_SHOW else ""
                    await update.message.reply_text(f"{preview}{tail}")
                context.user_data["wait_cang"] = False
                context.user_data["who_cang"] = None
                context.user_data["stage"] = None
                context.user_data["cang_list"] = []
                context.user_data["socang"] = None
        return

    if context.user_data.get("wait_latso", False):
        s = ''.join(re.findall(r'\d', text))
        if len(s) not in (3, 4):
            await update.message.reply_text("Chỉ nhập số có 3 hoặc 4 chữ số!")
        else:
            ketqua = sinh_lat_so(s)
            await update.message.reply_text(','.join(ketqua))
        context.user_data["wait_latso"] = False
        return

    if context.user_data.get("wait_gemini", False):
        if context.user_data.get("who_gemini", None) == user_id:
            count = context.user_data.get("gemini_count", 0)
            if count >= 10:
                await update.message.reply_text("Bạn đã hết lượt hỏi Thần tài trong phiên này (10/10)!\nVui lòng bấm /menu hoặc chọn lại chức năng để bắt đầu lại.")
                context.user_data["wait_gemini"] = False
                context.user_data["who_gemini"] = None
                context.user_data["gemini_count"] = 0
                return
            res = ask_gemini(text)
            await update.message.reply_text(f"💬 Thần tài trả lời ({count+1}/10):\n{res}")
            context.user_data["gemini_count"] = count + 1
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

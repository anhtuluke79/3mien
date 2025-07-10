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

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ==== ĐƯỜNG DẪN DỮ LIỆU AN TOÀN CHO RAILWAY ====
DATA_FILE = '/tmp/xsmb_full.csv'

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== HỎI GEMINI AI ====
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

# ==== TIỆN ÍCH GHÉP SỐ, PHONG THỦY, CAN CHI ====
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

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

# ==== CRAWL VÀ CẬP NHẬT XSMB 60 NGÀY ====
def crawl_xsmb_one_day(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="table-kq-xsmb")
    if not table:
        raise Exception("Không tìm thấy bảng kết quả!")
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

def crawl_new_days_csv(filename=DATA_FILE, max_pages=60):
    latest_date = get_latest_date_in_csv(filename)
    print(f"Ngày mới nhất đã có trong file: {latest_date.strftime('%d/%m/%Y') if latest_date else 'Chưa có dữ liệu'}")
    base_url = "https://xoso.com.vn/xo-so-mien-bac/xsmb-p{}.html"
    new_results = []
    for i in range(1, max_pages + 1):
        url = base_url.format(i)
        try:
            kq = crawl_xsmb_one_day(url)
            try:
                date_obj = datetime.datetime.strptime(kq["Ngày"], "%d/%m/%Y")
            except:
                print(f"Lỗi định dạng ngày: {kq['Ngày']} tại trang {url}")
                continue
            if latest_date and date_obj <= latest_date:
                print(f"Đã đến ngày cũ ({kq['Ngày']}), dừng crawl.")
                break
            print(f"Lấy mới ngày: {kq['Ngày']}")
            new_results.append(kq)
        except Exception as e:
            print(f"Lỗi ở trang {url}: {e}")
    if not new_results:
        print("Không có dữ liệu mới cần cập nhật.")
        return
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
    print(f"Đã cập nhật {len(df_new)} ngày mới vào {filename}")

# ==== AI CẦU LÔ: THỐNG KÊ LÔ THEO CHU KỲ ====
def thong_ke_lo(csv_file=DATA_FILE, days=7):
    if not os.path.exists(csv_file):
        crawl_new_days_csv(csv_file, 60)
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

# ==== GỬI FILE CSV CHO ADMIN (/download_csv HOẶC NÚT MENU) ====
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

# ==== BOT TELEGRAM HANDLER ==== 

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

    # ==== Download CSV (ADMIN) ====
    if query.data == "download_csv":
        await send_csv_callback(query, user_id)
        return

    # ==== AI CẦU LÔ ====
    if query.data == "ai_lo_menu":
        keyboard = [
            [
                InlineKeyboardButton("7 ngày", callback_data="ai_lo_7"),
                InlineKeyboardButton("14 ngày", callback_data="ai_lo_14"),
                InlineKeyboardButton("30 ngày", callback_data="ai_lo_30"),
                InlineKeyboardButton("60 ngày", callback_data="ai_lo_60"),
            ]
        ]
        await query.edit_message_text(
            "🤖 AI cầu lô - Chọn chu kỳ thống kê:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    if query.data.startswith("ai_lo_"):
        days = int(query.data.split("_")[-1])
        if not os.path.exists(DATA_FILE):
            await query.edit_message_text("Chưa có dữ liệu. Đang tự động tạo file xsmb_full.csv...")
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, crawl_new_days_csv, DATA_FILE, 60)
        xac_suat, lo_gan = thong_ke_lo(DATA_FILE, days)
        msg = f"🤖 Thống kê lô tô {days} ngày gần nhất:\n"
        msg += "- Top 10 lô ra nhiều nhất:\n"
        msg += "\n".join([f"  • {l}: {c} lần ({p}%)" for l,c,p in xac_suat])
        msg += f"\n- Các lô gan nhất (lâu chưa về): {', '.join(sorted(lo_gan)[:10])}..."
        await query.edit_message_text(msg)
        return

    # ==== Cập nhật XSMB (admin) ====
    if query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await query.edit_message_text("⏳ Đang cập nhật dữ liệu xsmb_full.csv (60 ngày)...")
        import asyncio
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, crawl_new_days_csv, DATA_FILE, 60)
        await query.edit_message_text("✅ Đã cập nhật dữ liệu xsmb_full.csv thành công (60 ngày mới nhất)!")
        return

    # ==== Thống kê ====
    if query.data == "thongke":
        if not os.path.exists(DATA_FILE):
            await query.edit_message_text("Chưa có dữ liệu. Đang tự động tạo file xsmb_full.csv...")
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, crawl_new_days_csv, DATA_FILE, 60)
        try:
            df = pd.read_csv(DATA_FILE)
            if 'Đặc biệt' not in df.columns or df['Đặc biệt'].isnull().all():
                await query.edit_message_text("Không có dữ liệu ĐB trong xsmb_full.csv.")
                return
            dbs = df['Đặc biệt'].astype(str).str[-2:]
            counts = dbs.value_counts().head(10)
            top_list = "\n".join([f"Số {i}: {v} lần" for i, v in counts.items()])
            today_db = dbs.iloc[0] if len(dbs) > 0 else "?"
            text = (
                f"📈 Top 10 số ĐB xuất hiện nhiều nhất 60 ngày gần nhất:\n{top_list}\n"
                f"\n🎯 Số ĐB hôm nay: {today_db}"
            )
            await query.edit_message_text(text)
        except Exception as e:
            await query.edit_message_text(f"Lỗi thống kê: {e}")
        return

    # ==== Dự đoán AI ====
    if query.data == "du_doan_ai":
        if not os.path.exists(DATA_FILE):
            await query.edit_message_text("Chưa có dữ liệu. Đang tự động tạo file xsmb_full.csv...")
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, crawl_new_days_csv, DATA_FILE, 60)
        try:
            df = pd.read_csv(DATA_FILE)
            df = df.dropna()
            df['Đặc biệt'] = df['Đặc biệt'].astype(str).str[-2:]
            df['Đặc biệt'] = df['Đặc biệt'].astype(int)
            if not os.path.exists('model_rf_loto.pkl'):
                await query.edit_message_text("Chưa có mô hình AI, cần train trước bằng lệnh /train_model.")
                return
            model = joblib.load('model_rf_loto.pkl')
            last7 = df['Đặc biệt'][:7].tolist()
            if len(last7) < 7:
                await query.edit_message_text("Không đủ dữ liệu 7 ngày để dự đoán!")
                return
            probs = model.predict_proba([last7])[0]
            top_idx = probs.argsort()[-3:][::-1]
            ketqua = [f"{model.classes_[i]:02d}" for i in top_idx]
            await query.edit_message_text(
                "🤖 Dự đoán AI (RandomForest) cho lần quay tiếp theo:\n"
                f"Top 3 số: {', '.join(ketqua)}"
            )
        except Exception as e:
            await query.edit_message_text(f"Lỗi dự đoán AI: {e}")
        return

    # ==== Các callback khác giữ nguyên như mẫu trước ====
    # ... (Không thay đổi các phần ghép xiên/càng, phong thủy, hỏi Gemini, train_model, ...)

    await query.edit_message_text("Chức năng này đang phát triển hoặc chưa được cấu hình!")

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Giữ nguyên các xử lý cũ (ghép xiên/càng, phong thủy, hỏi Gemini,...)
    pass

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("download_csv", send_csv))   # <-- Lệnh admin tải CSV
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), all_text_handler))
    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

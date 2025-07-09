import os
import logging
import requests
from bs4 import BeautifulSoup
from itertools import combinations
import random
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

# Thêm import AI
import joblib

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, ConversationHandler, filters
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Hoặc thay bằng token của bạn
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_gh_cang = {}
user_xien_data = {}
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
XIEN_TYPE, XIEN_NUMBERS = range(2)

# --- CRAWL DỮ LIỆU XSMB ---
def crawl_xsmn_me():
    url = "https://xsmn.me/lich-su-ket-qua-xsmb.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='tblKQ')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ xsmn.me")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl xsmn.me:", e)
        return None

def crawl_minhngoc():
    url = "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-bac.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='resultmb')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ minhngoc.net.vn")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl minhngoc.net.vn:", e)
        return None

def crawl_xosokt():
    url = "https://xosokt.net/xsmb-xo-so-mien-bac.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='bangketqua')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ xosokt.net")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl xosokt.net:", e)
        return None

def crawl_lich_su_xsmb(filename="xsmb.csv"):
    for func in [crawl_xsmn_me, crawl_minhngoc, crawl_xosokt]:
        df = func()
        if df is not None and not df.empty:
            if not os.path.exists(filename):
                df.to_csv(filename, index=False)
            else:
                df_old = pd.read_csv(filename)
                df_concat = pd.concat([df, df_old]).drop_duplicates(subset=["Ngày"])
                df_concat = df_concat.sort_values("Ngày", ascending=False)
                df_concat.to_csv(filename, index=False)
            print(f"Đã backup lịch sử XSMB vào {filename}")
            return True
    print("❌ Không crawl được dữ liệu từ bất kỳ nguồn nào!")
    return False

def doc_lich_su_xsmb_csv(filename="xsmb.csv", so_ngay=30):
    try:
        df = pd.read_csv(filename)
        if len(df) > so_ngay:
            df = df.head(so_ngay)
        return df
    except Exception as e:
        return None

# --- AI DỰ ĐOÁN ---
def du_doan_ai_with_model(df, model_path='xsmb_rf_model.pkl'):
    # Chuẩn hóa dữ liệu
    df = df.dropna()
    df['ĐB'] = df['ĐB'].astype(str).str[-2:]
    df['ĐB'] = df['ĐB'].astype(int)
    last7 = df['ĐB'][:7].tolist()
    if len(last7) < 7:
        return ["Không đủ dữ liệu 7 ngày!"]
    if not os.path.exists(model_path):
        return ["Chưa có mô hình AI, cần train trước!"]
    model = joblib.load(model_path)
    probs = model.predict_proba([last7])[0]
    top_idx = probs.argsort()[-3:][::-1]
    ketqua = [f"{model.classes_[i]:02d}" for i in top_idx]
    return ketqua

# --- BOT HANDLER ---

def get_kqxs_mienbac():
    url = "https://xsmn.mobi/xsmn-mien-bac"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="bkqmienbac")
        if not table:
            return {"error": "Không tìm thấy bảng kết quả"}
        results = {}
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                numbers = ' '.join(col.get_text(strip=True) for col in cols[1:])
                results[label] = numbers
        return results
    except Exception as e:
        return {"error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\nGõ /menu để bắt đầu."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Kết quả", callback_data="kqxs"),
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🧠 Dự đoán AI", callback_data="du_doan_ai"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
        ]
    ]
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text(f"❌ Lỗi: {result['error']}")
        return
    reply = "\n".join(f"{k}: {v}" for k, v in result.items())
    await update.message.reply_text(reply)
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
    await update.message.reply_text("Chọn thao tác tiếp theo:", reply_markup=InlineKeyboardMarkup(keyboard))

# GHÉP CÀNG - Conversation
async def ghepcang_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_gh_cang[user_id] = {}
    await update.message.reply_text("🔢 Nhập loại ghép (3D hoặc 4D):", reply_markup=ReplyKeyboardRemove())
    return GH_CANG_TYPE

async def ghepcang_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kieu = update.message.text.strip().upper()
    if kieu not in ["3D", "4D"]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 3D hoặc 4D. Nhập lại:")
        return GH_CANG_TYPE
    user_gh_cang[user_id]["kieu"] = kieu
    await update.message.reply_text("✏️ Nhập các số càng (VD: 3 4 hoặc 3,4):")
    return GH_CANG_LIST

async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cangs = [s.strip() for s in update.message.text.replace(',', ' ').split() if s.strip()]
    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng. Nhập lại (VD: 3 4 hoặc 3,4):")
        return GH_CANG_LIST
    user_gh_cang[user_id]["cangs"] = cangs
    await update.message.reply_text("✏️ Nhập các số cần ghép (VD: 123 456 hoặc 123,456):")
    return GH_SO_LIST

async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_gh_cang.get(user_id, {})
    kieu = data.get("kieu")
    numbers_raw = [s.strip() for s in update.message.text.replace(',', ' ').split() if s.strip()]
    if not numbers_raw or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Thiếu dữ liệu. Gõ lại từ đầu.")
        return ConversationHandler.END

    if kieu == "4D":
        numbers = [x for x in numbers_raw if len(x) == 3 and x.isdigit()]
        if len(numbers) != len(numbers_raw):
            await update.message.reply_text("⚠️ Mỗi số ghép cho 4D phải gồm đúng 3 chữ số (VD: 123 045 999). Nhập lại:")
            return GH_SO_LIST
    else:
        numbers = [x.zfill(3) for x in numbers_raw if x.isdigit()]

    results = []
    for cang in data["cangs"]:
        for num in numbers:
            if kieu == "3D":
                results.append(f"{cang}{num[-2:]}")
            elif kieu == "4D":
                results.append(f"{cang}{num}")
    await update.message.reply_text(', '.join(results) if results else "❌ Không có kết quả.")
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
    await update.message.reply_text("Chọn thao tác tiếp theo:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_gh_cang.pop(user_id, None)
    return ConversationHandler.END

# GHÉP XIÊN - Conversation
async def ghepxien_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_xien_data[user_id] = {}
    await update.message.reply_text("🔢 Nhập loại xiên (2, 3 hoặc 4):", reply_markup=ReplyKeyboardRemove())
    return XIEN_TYPE

async def ghepxien_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kieu = update.message.text.strip()
    if kieu not in ["2", "3", "4"]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 2, 3 hoặc 4. Nhập lại:")
        return XIEN_TYPE
    user_xien_data[user_id]["kieu"] = int(kieu)
    await update.message.reply_text("✏️ Nhập các số để ghép xiên (VD: 01 23 45 67 hoặc 01,23,45,67):")
    return XIEN_NUMBERS

async def ghepxien_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [s.strip() for s in update.message.text.replace(',', ' ').split() if s.strip()]
    data = user_xien_data.get(user_id, {})
    kieu = data.get("kieu")
    if not numbers or not kieu:
        await update.message.reply_text("❌ Thiếu dữ liệu. Gõ lại từ đầu.")
        return ConversationHandler.END
    if len(numbers) < kieu:
        await update.message.reply_text(f"❌ Cần ít nhất {kieu} số để ghép xiên {kieu}. Nhập lại:")
        return XIEN_NUMBERS
    xiens = list(combinations(numbers, kieu))
    result = [",".join(x) for x in xiens]
    await update.message.reply_text(', '.join(result) if result else "❌ Không có kết quả.")
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
    await update.message.reply_text("Chọn thao tác tiếp theo:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_xien_data.pop(user_id, None)
    return ConversationHandler.END

# DỰ ĐOÁN AI SỬ DỤNG MÔ HÌNH THẬT
async def du_doan_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = doc_lich_su_xsmb_csv()
    if df is None or df.empty:
        await update.message.reply_text("❌ Không đọc được dữ liệu lịch sử xổ số!")
        return
    so_du_doan = du_doan_ai_with_model(df)
    if "Không đủ dữ liệu" in so_du_doan[0] or "Chưa có mô hình" in so_du_doan[0]:
        text = f"⚠️ {so_du_doan[0]}"
    else:
        text = "🧠 AI dự đoán hôm nay: " + ', '.join(so_du_doan)
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)

# THỐNG KÊ ĐB
async def thong_ke_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = doc_lich_su_xsmb_csv()
    if df is None or df.empty:
        await update.message.reply_text("❌ Không đọc được dữ liệu lịch sử xổ số!")
        return
    db_counts = df['ĐB'].value_counts()
    reply = "🔢 Top 10 số ĐB xuất hiện nhiều nhất 30 ngày:\n"
    for so, count in db_counts.head(10).items():
        reply += f"{so}: {count} lần\n"
    await update.message.reply_text(reply)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔️ Đã hủy thao tác.")
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
    await update.message.reply_text("Quay lại menu:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data
    if cmd == "kqxs":
        await kqxs(update, context)
    elif cmd == "ghepcang":
        await ghepcang_popup(update, context)
    elif cmd == "ghepxien":
        await ghepxien_popup(update, context)
    elif cmd == "du_doan_ai":
        await du_doan_ai(update, context)
    elif cmd == "thongke":
        await thong_ke_db(update, context)
    elif cmd == "back_to_menu":
        await menu(update, context)
    else:
        await query.edit_message_text("❌ Không nhận diện được lựa chọn.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("thongke", thong_ke_db))
    # Ghép càng Conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepcang_popup, pattern="^ghepcang$")],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    # Ghép xiên Conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepxien_popup, pattern="^ghepxien$")],
        states={
            XIEN_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_type)],
            XIEN_NUMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_numbers)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.add_handler(CallbackQueryHandler(handle_menu_callback))

    # --- TỰ ĐỘNG UPDATE FILE CSV HÀNG NGÀY VỚI APSCHEDULER ---
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        crawl_lich_su_xsmb,
        'cron',
        hour=18, minute=50,
        id='update_xsmb_csv',
        replace_existing=True
    )
    scheduler.start()

    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    crawl_lich_su_xsmb()
    main()

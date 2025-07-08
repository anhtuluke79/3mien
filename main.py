import logging
import os
import requests
from itertools import combinations
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN chưa được thiết lập.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_gh_cang = {}
user_xien_data = {}
scheduler = BackgroundScheduler()
scheduler.start()

GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
XIEN_SO_LIST, XIEN_KIEU = range(2)

def get_kqxs_mienbac():
    url = "https://xsmn.mobi/xsmn-mien-bac"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="bkqmienbac")
        if not table:
            return {"error": "Không tìm thấy bảng kết quả"}
        results = {}
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                numbers = ' '.join(col.get_text(strip=True) for col in cols[1:])
                results[label] = numbers
        return results
    except Exception as e:
        return {"error": str(e)}

def download_lottery_image():
    try:
        url = "https://www.minhchinh.com/images/kqxsmb.jpg"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open("latest_kqxs.jpg", "wb") as f:
                f.write(response.content)
    except Exception as e:
        print("Tải ảnh lỗi:", e)

async def send_lottery_image(context: CallbackContext):
    chat_id = context.job.data.get("chat_id")
    download_lottery_image()
    image_path = "latest_kqxs.jpg"
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📸 Kết quả xổ số hôm nay")
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ Không có ảnh kết quả hôm nay.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Chào mừng bạn đến với XosoBot Telegram!
Gõ /menu để bắt đầu.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Kết quả", callback_data="kqxs"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang")
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🔢 Xiên nâng cao", callback_data="ghepxien_popup")
        ],
        [
            InlineKeyboardButton("🧠 AI gợi ý số", callback_data="goi_y_so_ai"),
            InlineKeyboardButton("🕒 Bật tự động", callback_data="bat_tudong")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Mời bạn chọn chức năng:", reply_markup=reply_markup)

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    reply = ""
    for label, val in result.items():
        reply += f"{label}: {val}
"
    await update.message.reply_text(reply)
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
    await update.message.reply_text("Chọn thao tác tiếp theo:", reply_markup=InlineKeyboardMarkup(keyboard))

# Ghép càng flow
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
    await update.message.reply_text("✏️ Nhập các số càng (VD: 3 4):")
    return GH_CANG_LIST

async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cangs = update.message.text.strip().split()
    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng. Nhập lại:")
        return GH_CANG_LIST
    user_gh_cang[user_id]["cangs"] = cangs
    await update.message.reply_text("✏️ Nhập các số cần ghép (VD: 123 456):")
    return GH_SO_LIST

async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [x.zfill(3) for x in update.message.text.strip().split() if x.isdigit()]
    data = user_gh_cang.get(user_id, {})
    if not numbers or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Thiếu dữ liệu. Gõ lại từ đầu.")
        return ConversationHandler.END

    results = []
    kieu = data["kieu"]
    for cang in data["cangs"]:
        for num in numbers:
            if kieu == "3D":
                results.append(f"{cang}{num[-2:]}")
            elif kieu == "4D":
                results.append(f"{cang}{num}")

    if not results:
        await update.message.reply_text("❌ Không có kết quả.")
    else:
        await update.message.reply_text(', '.join(results))
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu")]]
        await update.message.reply_text("Chọn thao tác tiếp theo:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_gh_cang.pop(user_id, None)
    return ConversationHandler.END

async def bat_tudong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    scheduler.add_job(
        send_lottery_image,
        trigger='cron',
        hour=18, minute=40,
        kwargs={"context": context, "chat_id": chat_id},
        id=f'xsmb_{chat_id}',
        replace_existing=True
    )
    await update.message.reply_text("✅ Đã bật gửi ảnh kết quả xổ số lúc 18:40 hàng ngày.")

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
        await query.edit_message_text("⏳ Đang phát triển...")
    elif cmd == "ghepxien_popup":
        await query.edit_message_text("⏳ Đang phát triển...")
    elif cmd == "bat_tudong":
        await bat_tudong(update, context)
    elif cmd == "goi_y_so_ai":
        await query.edit_message_text("🧠 Tính năng AI gợi ý số đang phát triển...")
    elif cmd == "back_to_menu":
        await menu(update, context)
    else:
        await query.edit_message_text("❌ Không nhận diện được lựa chọn.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(CallbackQueryHandler(handle_menu_callback))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepcang_popup, pattern="^ghepcang$")],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()
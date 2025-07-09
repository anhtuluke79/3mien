import logging
import os
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from itertools import combinations

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
            await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📸 📊 Xem kết quả xổ số hôm nay")
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ Không tìm thấy ảnh kết quả hôm nay.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Chào mừng bạn đến với bot Xổ Số Telegram!\nSử dụng lệnh /menu để bắt đầu.")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Xem kết quả", callback_data="kqxs"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang")
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🕒 Tự động gửi kết quả", callback_data="bat_tudong")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Vui lòng chọn chức năng bên dưới:", reply_markup=reply_markup)


async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    reply = ""
    for label, val in result.items():
        reply += f"{label}: {val}\n"
    await update.message.reply_text(reply)
    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))
    # Ghép càng
async def ghepcang_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_gh_cang[user_id] = {}
    await update.message.reply_text("🔢 Nhập loại ghép càng (3D hoặc 4D):", reply_markup=ReplyKeyboardRemove())
    return GH_CANG_TYPE


async def ghepcang_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kieu = update.message.text.strip().upper()
    if kieu not in ["3D", "4D"]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 3D hoặc 4D. Vui lòng nhập lại:")
        return GH_CANG_TYPE
    user_gh_cang[user_id]["kieu"] = kieu
    await update.message.reply_text("✏️ Nhập danh sách số càng (ngăn cách bằng dấu phẩy):")
    return GH_CANG_LIST


async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cangs = [x.strip() for x in update.message.text.strip().replace(',', ' ').split() if x.strip()]
    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng. Vui lòng nhập lại:")
        return GH_CANG_LIST
    user_gh_cang[user_id]["cangs"] = cangs
    await update.message.reply_text("✏️ Nhập các số để ghép (VD: 123 456):")
    return GH_SO_LIST


async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [x.zfill(3) for x in update.message.text.strip().split() if x.isdigit()]
    data = user_gh_cang.get(user_id, {})
    if not numbers or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Dữ liệu bị thiếu. Gõ lại từ đầu.")
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
        await update.message.reply_text("❌ Không có kết quả nào phù hợp.")
    else:
        await update.message.reply_text(', '.join(results))
        keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
        await update.message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_gh_cang.pop(user_id, None)
    return ConversationHandler.END


# Ghép xiên
async def ghepxien_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_xien_data[user_id] = {}
    await update.message.reply_text("🔢 Nhập các số muốn ghép (VD: 22,33,44):")
    return XIEN_SO_LIST


async def ghepxien_sos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [x.strip() for x in update.message.text.strip().replace(',', ' ').split() if x.strip()]
    if len(numbers) < 2:
        await update.message.reply_text("⚠️ Bạn cần nhập ít nhất 2 số. Nhập lại:")
        return XIEN_SO_LIST
    user_xien_data[user_id]["numbers"] = numbers
    await update.message.reply_text("🔢 Nhập kiểu xiên (2, 3 hoặc 4):")
    return XIEN_KIEU


async def ghepxien_kieu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_xien_data.get(user_id, {})
    numbers = data.get("numbers", [])
    try:
        kieu = int(update.message.text.strip())
        if kieu < 2 or kieu > len(numbers):
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Kiểu xiên không hợp lệ. Nhập số 2, 3 hoặc 4:")
        return XIEN_KIEU

    result = [ '&'.join(combo) for combo in combinations(numbers, kieu) ]
    result_text = ', '.join(result)
    await update.message.reply_text(result_text)

    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("👉 Bạn muốn làm gì tiếp?", reply_markup=InlineKeyboardMarkup(keyboard))

    user_xien_data.pop(user_id, None)
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
    await update.message.reply_text("✅ Đã bật gửi ảnh kết quả lúc 18:40 mỗi ngày.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔️ Đã hủy bỏ thao tác hiện tại.")
    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("⬅️ Trở về menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))
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
        await ghepxien_start(update, context)
    elif cmd == "bat_tudong":
        await bat_tudong(update, context)
    elif cmd == "back_to_menu":
        await menu(update, context)
    else:
        await query.edit_message_text("❌ Lựa chọn không hợp lệ, vui lòng thử lại.")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("kqxs", kqxs))
    app.add_handler(CommandHandler("ghepcang", ghepcang_popup))
    app.add_handler(CommandHandler("ghepxien", ghepxien_start))

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

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepxien_start, pattern="^ghepxien$")],
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sos)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()

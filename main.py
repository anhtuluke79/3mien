
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
    ForceReply,
    ReplyKeyboardMarkup,
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

user_inputs = {}
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
    menu_keyboard = [
        ["📊 Kết quả", "➕ Ghép xiên"],
        ["🎯 Ghép càng", "🕒 Bật tự động"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("📋 Mời bạn chọn chức năng:", reply_markup=reply_markup)

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📊 Kết quả":
        await kqxs(update, context)
    elif text == "➕ Ghép xiên":
        await ghepxien_popup(update, context)
    elif text == "🎯 Ghép càng":
        await ghepcang_popup(update, context)
    elif text == "🕒 Bật tự động":
        await bat_tudong(update, context)
    else:
        await update.message.reply_text("❓ Không rõ bạn chọn gì. Gõ /menu để chọn lại.")

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    reply = "🎰 Kết quả miền Bắc hôm nay:
"
    for label, val in result.items():
        reply += f"{label}: {val}
"
    await update.message.reply_text(reply)

async def ghepxien_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_xien_data[user_id] = {}
    await update.message.reply_text("✏️ Nhập dãy số bạn muốn ghép xiên (VD: 12 34 56):")
    return XIEN_SO_LIST

async def ghepxien_sonhap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [n for n in update.message.text.strip().split() if n.isdigit()]
    if len(numbers) < 2:
        await update.message.reply_text("⚠️ Cần ít nhất 2 số.")
        return XIEN_SO_LIST
    user_xien_data[user_id]['numbers'] = numbers
    keyboard = [["2", "3", "4"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🔢 Chọn kiểu xiên (2, 3 hoặc 4):", reply_markup=reply_markup)
    return XIEN_KIEU

async def ghepxien_kieu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        kieu = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Nhập sai. Hãy nhập 2, 3 hoặc 4.")
        return XIEN_KIEU

    if kieu not in [2, 3, 4]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 2, 3 hoặc 4.")
        return XIEN_KIEU
    numbers = user_xien_data[user_id]['numbers']
    if len(numbers) < kieu:
        await update.message.reply_text(f"⚠️ Cần ít nhất {kieu} số.")
        return ConversationHandler.END
    xiens = list(combinations(numbers, kieu))
    formatted = [ '&'.join(x) for x in xiens ]
    result = ', '.join(formatted)
    await update.message.reply_text(f"🎯 Kết quả xiên {kieu}:
{result}")
    user_xien_data.pop(user_id, None)
    return ConversationHandler.END

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
    await update.message.reply_text("✏️ Nhập các số càng (VD: 1 2):")
    return GH_CANG_LIST

async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cangs = update.message.text.strip().split()
    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng. Nhập lại:")
        return GH_CANG_LIST
    user_gh_cang[user_id]["cangs"] = cangs
    await update.message.reply_text("✏️ Nhập các số lô cần ghép (VD: 23 45):")
    return GH_SO_LIST

async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = [x.zfill(2) for x in update.message.text.strip().split() if x.isdigit()]
    data = user_gh_cang.get(user_id, {})
    if not numbers or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Thiếu dữ liệu. Gõ lại /ghepcang_popup để bắt đầu.")
        return ConversationHandler.END

    results = []
    kieu = data["kieu"]
    for cang in data["cangs"]:
        for num in numbers:
            if kieu == "3D" and len(cang) == 1:
                results.append(f"{cang}{num}")
            elif kieu == "4D" and len(cang) == 2:
                results.append(f"{cang}{num}")

    if not results:
        await update.message.reply_text("❌ Không có kết quả. Kiểm tra lại dữ liệu.")
    else:
        await update.message.reply_text(f"🔢 Kết quả ghép {kieu}:
{', '.join(results)}")
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
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.REPLY, handle_menu_selection))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎯 Ghép càng$"), ghepcang_popup)],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Ghép xiên$"), ghepxien_popup)],
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sonhap)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

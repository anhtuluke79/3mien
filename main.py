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
    ReplyKeyboardMarkup, # Added for consistency
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler # Moved here
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Initialize scheduler globally
scheduler = BackgroundScheduler()
scheduler.start()

# --- Conversation States ---
# States for ghepxien_popup
XIEN_SO_LIST, XIEN_KIEU = range(2)

# States for ghepcang_popup
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)

# --- Utility Functions ---
def get_kqxs_mienbac():
    url = "https://xsmn.mobi/xsmn-mien-bac"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="bkqmienbac")
        if not table:
            logger.warning("Không tìm thấy bảng kết quả xổ số trên trang web.")
            return {"error": "Không tìm thấy bảng kết quả trên trang web. Vui lòng thử lại sau."}
        results = {}
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                numbers = ' '.join(col.get_text(strip=True) for col in cols[1:])
                results[label] = numbers
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi kết nối hoặc nhận phản hồi từ trang web: {e}")
        return {"error": f"Lỗi kết nối: {e}. Vui lòng thử lại sau."}
    except Exception as e:
        logger.error(f"Lỗi khi phân tích cú pháp kết quả xổ số: {e}")
        return {"error": f"Lỗi xử lý dữ liệu: {e}. Vui lòng thử lại sau."}

def download_lottery_image():
    try:
        url = "https://www.minhchinh.com/images/kqxsmb.jpg"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open("latest_kqxs.jpg", "wb") as f:
                f.write(response.content)
        logger.info("Ảnh kết quả xổ số đã được tải xuống.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi tải ảnh: {e}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải ảnh: {e}")

# --- Telegram Handlers ---

async def send_lottery_image(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data.get("chat_id")
    if not chat_id:
        logger.error("Không tìm thấy chat_id trong job data để gửi ảnh.")
        return

    download_lottery_image()
    image_path = "latest_kqxs.jpg"
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img:
                await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📸 Kết quả xổ số hôm nay")
            logger.info(f"Đã gửi ảnh KQXS đến chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Lỗi khi gửi ảnh đến chat_id {chat_id}: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ Lỗi khi gửi ảnh kết quả hôm nay.")
    else:
        logger.warning(f"Không tìm thấy file ảnh tại {image_path} để gửi đến chat_id: {chat_id}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Không có ảnh kết quả hôm nay để gửi.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Chào mừng bạn đến với XosoBot Telegram!\nGõ /menu để bắt đầu.")

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
        # Start the conversation for ghepxien_popup
        await ghepxien_popup(update, context)
    elif text == "🎯 Ghép càng":
        # Start the conversation for ghepcang_popup
        await ghepcang_popup(update, context)
    elif text == "🕒 Bật tự động":
        await bat_tudong(update, context)
    else:
        await update.message.reply_text("❓ Không rõ bạn chọn gì. Gõ /menu để chọn lại.")

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Use query.message if it's from a callback, otherwise update.message
    message_to_reply = update.callback_query.message if update.callback_query else update.message

    result = get_kqxs_mienbac()
    if "error" in result:
        await message_to_reply.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    reply = "🎰 Kết quả miền Bắc hôm nay:\n\n"
    for label, val in result.items():
        reply += f"{label}: {val}\n"
    await message_to_reply.reply_text(reply)

# Removed the old `ghepxien` and `handle_reply` functions as ConversationHandler is preferred.
# The `xi_handler` (inline button version) is also removed as it's replaced by `ghepxien_kieu` in ConversationHandler.

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
    logger.info(f"Đã lên lịch gửi ảnh KQXS cho chat_id: {chat_id}")

# --- Ghepcang (Conversation Handler version) ---
async def ghepcang_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Using context.user_data for state management
    context.user_data['ghepcang'] = {}
    await update.message.reply_text("🔢 Nhập loại ghép (3D hoặc 4D):", reply_markup=ReplyKeyboardRemove())
    return GH_CANG_TYPE

async def ghepcang_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kieu = update.message.text.strip().upper()
    if kieu not in ["3D", "4D"]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 3D hoặc 4D. Nhập lại:")
        return GH_CANG_TYPE
    context.user_data['ghepcang']["kieu"] = kieu
    await update.message.reply_text("✏️ Nhập các số càng (VD: 1 2):")
    return GH_CANG_LIST

async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cangs = update.message.text.strip().split()
    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng. Nhập lại:")
        return GH_CANG_LIST
    context.user_data['ghepcang']["cangs"] = cangs
    await update.message.reply_text("✏️ Nhập các số lô cần ghép (VD: 23 45):")
    return GH_SO_LIST

async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = [x.zfill(2) for x in update.message.text.strip().split() if x.isdigit()]
    data = context.user_data.get('ghepcang', {})

    if not numbers or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Thiếu dữ liệu hoặc phiên đã hết hạn. Gõ lại /menu để bắt đầu.")
        context.user_data.pop('ghepcang', None) # Clean up
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
        await update.message.reply_text(f"🔢 Kết quả ghép {kieu}:\n\n{', '.join(results)}")

    context.user_data.pop('ghepcang', None) # Clean up
    return ConversationHandler.END

# --- Ghepxien (Conversation Handler version) ---
async def ghepxien_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ghepxien'] = {}
    await update.message.reply_text("✏️ Nhập dãy số bạn muốn ghép xiên (VD: 12 34 56):")
    return XIEN_SO_LIST

async def ghepxien_sonhap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = [n for n in update.message.text.strip().split() if n.isdigit()]
    if len(numbers) < 2:
        await update.message.reply_text("⚠️ Cần ít nhất 2 số để ghép xiên. Vui lòng nhập lại:")
        return XIEN_SO_LIST
    context.user_data['ghepxien']['numbers'] = numbers
    keyboard = [["2", "3", "4"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🔢 Chọn kiểu xiên (2, 3 hoặc 4):", reply_markup=reply_markup)
    return XIEN_KIEU

async def ghepxien_kieu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kieu = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Kiểu xiên không hợp lệ. Vui lòng nhập 2, 3 hoặc 4:")
        return XIEN_KIEU

    if kieu not in [2, 3, 4]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận xiên 2, 3 hoặc 4. Vui lòng nhập lại:")
        return XIEN_KIEU

    numbers = context.user_data['ghepxien']['numbers']
    if len(numbers) < kieu:
        await update.message.reply_text(f"⚠️ Cần ít nhất {kieu} số để tạo xiên {kieu}. Vui lòng nhập lại dãy số hoặc chọn kiểu xiên khác.")
        context.user_data.pop('ghepxien', None) # Clean up
        return ConversationHandler.END

    xiens = list(combinations(numbers, kieu))
    formatted = [ '&'.join(x) for x in xiens ]
    result = ', '.join(formatted)
    await update.message.reply_text(f"🎯 Kết quả xiên {kieu}:\n\n{result}")

    context.user_data.pop('ghepxien', None) # Clean up
    return ConversationHandler.END

def main():
    # Ensure TELEGRAM_TOKEN is set
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set. Please set it before running the bot.")
        return

    # 1. Build the Application instance FIRST
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    logger.info("Bot Application built successfully.")

    # 2. Define Conversation Handlers
    conv_xien = ConversationHandler(
        entry_points=[
            CommandHandler("ghepxien_popup", ghepxien_popup),
            MessageHandler(filters.Regex("^➕ Ghép xiên$"), ghepxien_popup) # Entry point from menu button
        ],
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sonhap)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[], # Add fallbacks if needed for cancellation/error
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END # Allows child conversation to end parent if applicable
        }
    )

    conv_ghepcang = ConversationHandler(
        entry_points=[
            CommandHandler("ghepcang_popup", ghepcang_popup),
            MessageHandler(filters.Regex("^🎯 Ghép càng$"), ghepcang_popup) # Entry point from menu button
        ],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[], # Add fallbacks if needed for cancellation/error
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    # 3. Add Handlers to the Application (Order matters!)
    # Specific command handlers first
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))

    # Add Conversation Handlers
    app.add_handler(conv_xien)
    app.add_handler(conv_ghepcang)

    # Callback Query Handlers (for inline buttons, if any remain or are added)
    # The original button_handler for 'kqxs' is now handled by the menu selection
    app.add_handler(CallbackQueryHandler(kqxs, pattern="^kqxs$")) # Kept this for direct 'kqxs' callback if needed

    # Message Handler for menu selection (should be general but after specific ones)
    # This handler should only catch messages that are *not* commands and *not* replies to specific messages
    # and are part of the main menu keyboard. Using Regex for specific menu buttons is safer.
    app.add_handler(MessageHandler(filters.Regex("^(📊 Kết quả|➕ Ghép xiên|🎯 Ghép càng|🕒 Bật tự động)$"), handle_menu_selection))

    # Fallback for unhandled text messages (optional, but good for debugging)
    # Be careful with this, as it can catch messages intended for conversation handlers if filters are not precise.
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))


    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

import logging
import os
import requests
import joblib
from itertools import combinations
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
    InputFile,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ChatAction
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
user_inputs = {} # Used for inline keyboard based ghepxien
scheduler = BackgroundScheduler()
scheduler.start()

# ConversationHandler states for ghepcang_popup
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
user_gh_cang = {}

# ConversationHandler states for ghepxien_popup
XIEN_SO_LIST, XIEN_KIEU = range(2)
user_xien_data = {}


def get_kqxs_mienbac():
    url = "https://xsmn.mobi/xsmn-mien-bac"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi lấy kết quả (RequestException): {e}")
        return {"error": f"Lỗi kết nối: {e}"}
    except Exception as e:
        logger.error(f"Lỗi khi lấy kết quả: {e}")
        return {"error": str(e)}

def download_lottery_image():
    try:
        url = "https://www.minhchinh.com/images/kqxsmb.jpg"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open("latest_kqxs.jpg", "wb") as f:
            f.write(response.content)
        logger.info("Ảnh kết quả xổ số đã được tải.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Tải ảnh lỗi (RequestException): {e}")
    except Exception as e:
        logger.error(f"Tải ảnh lỗi: {e}")

async def send_lottery_image(context: CallbackContext):
    chat_id = context.job.data.get("chat_id")
    download_lottery_image()
    image_path = "latest_kqxs.jpg"
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📸 Kết quả xổ số hôm nay")
        os.remove(image_path) # Clean up the downloaded image
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ Không có ảnh kết quả hôm nay.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fixed the unterminated string literal error
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
        await ghepxien_popup(update, context) # Directs to the ConversationHandler entry
    elif text == "🎯 Ghép càng":
        await ghepcang_popup(update, context) # Directs to the ConversationHandler entry
    elif text == "🕒 Bật tự động":
        await bat_tudong(update, context)
    else:
        await update.message.reply_text("❓ Không rõ bạn chọn gì. Gõ /menu để chọn lại.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data
    if cmd == 'kqxs':
        await kqxs(update, context)
    elif cmd == 'ghepxien':
        # This is for the old inline keyboard based ghepxien, not used with new menu
        # If you still want it, ensure its entry is explicitly handled or removed
        await ghepxien(update, context) # This calls the original inline keyboard based ghepxien
    else:
        await query.edit_message_text("⚠️ Tính năng đang cập nhật.")

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    reply = "🎰 Kết quả miền Bắc hôm nay:\n"
    for label, val in result.items():
        reply += f"{label}: {val}\n"
    await update.message.reply_text(reply)

# Original inline keyboard based ghepxien (can be removed if only using popup)
async def ghepxien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_inputs[user_id] = {}
    await update.message.reply_text("✍️ Nhập dãy số bạn muốn ghép xiên (VD: 12 34 56 78)", reply_markup=ForceReply(selective=True))

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_inputs:
        # This handles replies not part of the `ghepxien` conversation started by ForceReply
        # It's better to use ConversationHandler for structured inputs
        return

    numbers = [n for n in update.message.text.strip().split() if n.isdigit()]
    if len(numbers) < 2:
        await update.message.reply_text("⚠️ Cần ít nhất 2 số.")
        return
    user_inputs[user_id]['numbers'] = numbers
    keyboard = [
        [InlineKeyboardButton("Xiên 2", callback_data=f"xi={user_id}=2"),
         InlineKeyboardButton("Xiên 3", callback_data=f"xi={user_id}=3"),
         InlineKeyboardButton("Xiên 4", callback_data=f"xi={user_id}=4")]
    ]
    await update.message.reply_text("🔢 Chọn kiểu xiên:", reply_markup=InlineKeyboardMarkup(keyboard))

async def xi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("=")
    if len(parts) != 3:
        return
    user_id, kieu = int(parts[1]), int(parts[2])
    if user_id not in user_inputs or 'numbers' not in user_inputs[user_id]:
        await query.edit_message_text("❌ Lỗi dữ liệu hoặc chưa nhập số.")
        return
    numbers = user_inputs[user_id]['numbers']
    if len(numbers) < kieu:
        await query.edit_message_text(f"⚠️ Cần ít nhất {kieu} số.")
        return
    xiens = list(combinations(numbers, kieu))
    formatted = [ '&'.join(x) for x in xiens ]
    result_text = ", ".join(formatted)
    await query.edit_message_text(f"🎯 Kết quả xiên {kieu}:\n{result_text}")
    del user_inputs[user_id]


async def bat_tudong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Check if a job for this chat_id already exists to prevent duplicates
    job_id = f'xsmb_{chat_id}'
    if scheduler.get_job(job_id):
        await update.message.reply_text("🔄 Chức năng tự động đã được bật rồi. Để tắt, bạn cần khởi động lại bot (hoặc thêm chức năng tắt).")
        return

    scheduler.add_job(
        send_lottery_image,
        trigger='cron',
        hour=18, minute=40,
        kwargs={"context": context, "chat_id": chat_id},
        id=job_id,
        replace_existing=True
    )
    await update.message.reply_text("✅ Đã bật gửi ảnh kết quả xổ số lúc 18:40 hàng ngày.")

def ghep_cang_tuy_chinh(numbers, cang_list, kieu="3D"):
    result = []
    for cang in cang_list:
        # Ensure 'cang' is a string for length check
        cang_str = str(cang)
        for num in numbers:
            # Ensure 'num' is a string and zero-padded for 2 digits
            num_str = str(num).zfill(2)
            if kieu == "3D" and len(cang_str) == 1:
                result.append(f"{cang_str}{num_str}")
            elif kieu == "4D" and len(cang_str) == 2:
                result.append(f"{cang_str}{num_str}")
    return result

async def ghepcang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if not text or "|" not in text:
        await update.message.reply_text("❌ Sai cú pháp.\nGõ: /ghepcang <3D|4D> <càng...> | <số...>\nVD: /ghepcang 3D 1 2 | 23 45")
        return
    try:
        parts = text.split("|")
        left_part = parts[0].strip().split()
        right_part = parts[1].strip().split()

        if not left_part:
            await update.message.reply_text("⚠️ Cần xác định loại ghép (3D/4D).")
            return

        kieu = left_part[0].upper()
        if kieu not in ["3D", "4D"]:
            await update.message.reply_text("⚠️ Loại ghép không hợp lệ. Chỉ chấp nhận 3D hoặc 4D.")
            return

        cang_list = [x for x in left_part[1:] if x.isdigit()]
        numbers = [x.zfill(2) for x in right_part if x.isdigit()]

        if not cang_list:
            await update.message.reply_text("⚠️ Thiếu số càng.")
            return
        if not numbers:
            await update.message.reply_text("⚠️ Thiếu số lô.")
            return

        results = ghep_cang_tuy_chinh(numbers, cang_list, kieu)
        if not results:
            await update.message.reply_text("❌ Không có kết quả. Kiểm tra lại cú pháp hoặc dữ liệu nhập.")
            return

        formatted = ', '.join(results)
        await update.message.reply_text(f"🔢 Kết quả ghép {kieu}:\n{formatted}")

    except Exception as e:
        logger.error(f"Lỗi xử lý /ghepcang: {e}")
        await update.message.reply_text(f"❌ Lỗi xử lý: {e}. Vui lòng thử lại hoặc kiểm tra cú pháp.")


# --- Conversation Handlers for popup style interactions ---

# Ghepcang Popup Handlers
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
        await update.message.reply_text("❌ Thiếu dữ liệu. Vui lòng chọn '🎯 Ghép càng' từ menu để bắt đầu lại.")
        # Ensure the conversation ends cleanly
        user_gh_cang.pop(user_id, None)
        return ConversationHandler.END

    results = []
    kieu = data["kieu"]
    for cang in data["cangs"]:
        cang_str = str(cang) # Ensure string conversion
        for num in numbers:
            num_str = str(num).zfill(2) # Ensure string conversion and zero-padding
            if kieu == "3D" and len(cang_str) == 1:
                results.append(f"{cang_str}{num_str}")
            elif kieu == "4D" and len(cang_str) == 2:
                results.append(f"{cang_str}{num_str}")

    if not results:
        await update.message.reply_text("❌ Không có kết quả. Kiểm tra lại dữ liệu.")
    else:
        await update.message.reply_text(f"🔢 Kết quả ghép {kieu}:\n{', '.join(results)}")
    user_gh_cang.pop(user_id, None)
    return ConversationHandler.END

# Ghepxien Popup Handlers
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
        await update.message.reply_text("⚠️ Kiểu xiên không hợp lệ. Vui lòng nhập 2, 3 hoặc 4.")
        return XIEN_KIEU

    if kieu not in [2, 3, 4]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận 2, 3 hoặc 4.")
        return XIEN_KIEU

    numbers = user_xien_data.get(user_id, {}).get('numbers')
    if not numbers:
        await update.message.reply_text("❌ Dữ liệu số bị mất. Vui lòng chọn '➕ Ghép xiên' từ menu để bắt đầu lại.")
        user_xien_data.pop(user_id, None)
        return ConversationHandler.END

    if len(numbers) < kieu:
        await update.message.reply_text(f"⚠️ Cần ít nhất {kieu} số để ghép xiên {kieu}.")
        user_xien_data.pop(user_id, None)
        return ConversationHandler.END

    xiens = list(combinations(numbers, kieu))
    formatted = [ '&'.join(x) for x in xiens ]
    result = ', '.join(formatted)
    await update.message.reply_text(f"🎯 Kết quả xiên {kieu}:\n{result}")
    user_xien_data.pop(user_id, None)
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ConversationHandler for ghép xiên (popup style)
    conv_xien_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Ghép xiên$"), ghepxien_popup)], # Entry via menu selection
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sonhap)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[], # You might want to add a CommandHandler('cancel', cancel) here
    )
    app.add_handler(conv_xien_handler)

    # ConversationHandler for ghép càng (popup style)
    conv_cang_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎯 Ghép càng$"), ghepcang_popup)], # Entry via menu selection
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[], # You might want to add a CommandHandler('cancel', cancel) here
    )
    app.add_handler(conv_cang_handler)

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("kqxs", kqxs))
    app.add_handler(CommandHandler("ghepcang", ghepcang)) # Keep command for direct use if desired
    app.add_handler(CommandHandler("ghepxien", ghepxien)) # Keep command for direct use if desired (inline keyboard style)
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))

    # Handlers for menu and inline callbacks
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection))
    # The `handle_reply` and `xi_handler` are for the *original* inline keyboard based /ghepxien
    # If you fully transition to the ConversationHandler for ghepxien_popup, you might remove these.
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_reply))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(du_doan|kqxs|ghepxien)$"))
    app.add_handler(CallbackQueryHandler(xi_handler, pattern="^xi=\d+=\d+$"))


    logger.info("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

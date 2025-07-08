
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
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
user_inputs = {}
scheduler = BackgroundScheduler()
scheduler.start()

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
        print(f"Lỗi khi lấy kết quả: {e}")
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
    await update.message.reply_text("✨ Chào mừng bạn đến với XosoBot Telegram!\nGõ /menu để bắt đầu.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Dự đoán số", callback_data='du_doan')],
        [InlineKeyboardButton("🎰 Kết quả", callback_data='kqxs'),
         InlineKeyboardButton("➕ Ghép xiên", callback_data='ghepxien')]
    ]
    await update.message.reply_text("📋 Menu chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data
    if cmd == 'kqxs':
        await kqxs(update, context)
    elif cmd == 'ghepxien':
        await ghepxien(update, context)
    else:
        await query.edit_message_text("⚠️ Tính năng đang cập nhật.")

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text("❌ Lỗi khi lấy kết quả.")
        return
    reply = "🎰 Kết quả miền Bắc hôm nay:\n"
    for label, val in result.items():
        reply += f"{label}: {val}
"
    await update.message.reply_text(reply)

async def ghepxien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_inputs[user_id] = {}
    await update.message.reply_text("✍️ Nhập dãy số bạn muốn ghép xiên (VD: 12 34 56 78)", reply_markup=ForceReply(selective=True))

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_inputs:
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
    from itertools import combinations
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
    await query.edit_message_text(f"🎯 Kết quả xiên {kieu}:
{result_text}")
    del user_inputs[user_id]


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

def ghep_cang_tuy_chinh(numbers, cang_list, kieu="3D"):
    result = []
    for cang in cang_list:
        for num in numbers:
            if kieu == "3D" and len(cang) == 1:
                result.append(f"{cang}{num}")
            elif kieu == "4D" and len(cang) == 2:
                result.append(f"{cang}{num}")
    return result

async def ghepcang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if "|" not in text:
        await update.message.reply_text("❌ Sai cú pháp.
Gõ: /ghepcang <3D|4D> <càng...> | <số...>
VD: /ghepcang 3D 1 2 | 23 45")
        return
    try:
        parts = text.split("|")
        left = parts[0].strip().split()
        right = parts[1].strip().split()

        kieu = left[0].upper()
        cang_list = [x for x in left[1:] if x.isdigit()]
        numbers = [x.zfill(2) for x in right if x.isdigit()]

        if not cang_list or not numbers:
            await update.message.reply_text("⚠️ Thiếu số càng hoặc số lô.")
            return

        results = ghep_cang_tuy_chinh(numbers, cang_list, kieu)
        if not results:
            await update.message.reply_text("❌ Không có kết quả. Kiểm tra lại cú pháp.")
            return

        formatted = ', '.join(results)
        await update.message.reply_text(f"🔢 Kết quả ghép {kieu}:\n{formatted}")

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi xử lý: {e}")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ Chưa cấu hình TELEGRAM_TOKEN.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Menu dạng bàn phím ảo
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.REPLY, handle_menu_selection))

    # Ghép xiên dạng popup
    conv_xien = ConversationHandler(
        entry_points=[CommandHandler("ghepxien_popup", ghepxien_popup)],
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sonhap)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_xien)


    

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ghepcang_popup", ghepcang_popup)],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("kqxs", kqxs))
    app.add_handler(CommandHandler("ghepxien", ghepxien))
    app.add_handler(CommandHandler("ghepcang", ghepcang))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_reply))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(du_doan|kqxs|ghepxien)$"))
    app.add_handler(CallbackQueryHandler(xi_handler, pattern="^xi=\d+=\d+$"))
    print("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()




from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters

# Các trạng thái cho popup nhập càng
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
user_gh_cang = {}

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


, ReplyKeyboardRemove

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






XIEN_SO_LIST, XIEN_KIEU = range(2)
user_xien_data = {}

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
    from itertools import combinations
    user_id = update.effective_user.id
    kieu = int(update.message.text.strip())
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
    await update.message.reply_text(f"🎯 Kết quả xiên {kieu}:\n{result}")
    user_xien_data.pop(user_id, None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔️ Đã hủy thao tác.")
    return ConversationHandler.END

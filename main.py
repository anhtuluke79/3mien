import logging
import os
import random
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

def predict_mb_advanced():
    try:
        model = joblib.load("model_rf_loto.pkl")
        sample = [[12, 34, 56, 78, 89, 90, 11]]
        prediction = model.predict(sample)
        return [str(p).zfill(2) for p in prediction[:5]]
    except Exception as e:
        print(f"Lỗi AI: {e}")
        return ["??"]

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
        [InlineKeyboardButton("📊 Gợi ý AI", callback_data='goi_y_so_ai'),
         InlineKeyboardButton("🎯 Dự đoán số", callback_data='du_doan')],
        [InlineKeyboardButton("🎰 Kết quả", callback_data='kqxs'),
         InlineKeyboardButton("➕ Ghép xiên", callback_data='ghepxien')]
    ]
    await update.message.reply_text("📋 Menu chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data
    if cmd == 'goi_y_so_ai':
        await goi_y_so_ai(update, context)
    elif cmd == 'du_doan':
        await query.edit_message_text("✏️ Gõ /du_doan <số> để dự đoán")
    elif cmd == 'kqxs':
        await kqxs(update, context)
    elif cmd == 'ghepxien':
        await ghepxien(update, context)

async def goi_y_so_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suggestions = predict_mb_advanced()
    await update.message.reply_text("📊 Gợi ý từ AI:\n" + ", ".join(suggestions))

async def kqxs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_kqxs_mienbac()
    if "error" in result:
        await update.message.reply_text("❌ Lỗi khi lấy kết quả.")
        return
    reply = "🎰 Kết quả miền Bắc hôm nay:\n"
    for label, val in result.items():
        reply += f"{label}: {val}\n"
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
    formatted = [' & '.join(x) for x in xiens]
    await query.edit_message_text(f"🎯 Kết quả xiên {kieu}:\n" + "\n".join(formatted))
    del user_inputs[user_id]

async def du_doan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Gõ: /du_doan <số>")
        return
    number = context.args[0]
    await update.message.reply_text(f"✅ Đã ghi nhận số bạn dự đoán: {number}")

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

def main():
    app.add_handler(CommandHandler("ghepcang", ghepcang))
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("goi_y_so_ai", goi_y_so_ai))
    app.add_handler(CommandHandler("du_doan", du_doan))
    app.add_handler(CommandHandler("kqxs", kqxs))
    app.add_handler(CommandHandler("ghepxien", ghepxien))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_reply))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(goi_y_so_ai|du_doan|kqxs|ghepxien)$"))
    app.add_handler(CallbackQueryHandler(xi_handler, pattern="^xi=\d+=\d+$"))
    print("🚀 Bot Telegram đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()


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
        await update.message.reply_text("❌ Sai cú pháp.\nGõ: /ghepcang <3D|4D> <càng...> | <số...>\nVD: /ghepcang 3D 1 2 | 23 45")
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

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
    await update.message.reply_text("✨ Chào mừng bạn đến với bot Xổ Số Telegram! Sử dụng lệnh /menu để bắt đầu.")


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
        # Sửa lỗi bằng cách thêm '\n' vào cuối chuỗi
        reply += f"{label}: {val}\n"
        
    # Gửi tin nhắn chứa kết quả sau khi vòng lặp kết thúc
    await update.message.reply_text(reply)

    await update.message.reply_text(reply)
    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))

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

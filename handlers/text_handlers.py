import asyncio
import os
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ==== Import các handler đã viết sẵn từ các file module riêng ==== #
from handlers.menu import menu, admin_menu, menu_callback_handler

# ==== Thiết lập logger ====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==== Đọc biến môi trường ====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

raw_admin_ids = os.getenv("ADMIN_IDS")
if not raw_admin_ids:
    raise ValueError("ADMIN_IDS chưa được thiết lập!")
ADMIN_IDS = list(map(int, raw_admin_ids.split(',')))

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ==== Giao diện chính ==== #
def main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

# ==== Hàm khởi chạy chính ==== #
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Các lệnh người dùng
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))

    # Inline menu và callback
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Tin nhắn dạng văn bản khi đang ở trạng thái nhập liệu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    # Chạy bot
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

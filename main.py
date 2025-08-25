import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)
from handlers.menu import menu, menu_callback

# Bật log để debug khi chạy trên Railway
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")  # Lấy token từ biến môi trường Railway

def main():
    # Tạo bot application
    application = Application.builder().token(TOKEN).build()

    # Handler cho /menu
    application.add_handler(CommandHandler("menu", menu))

    # Handler cho các callback nút bấm
    application.add_handler(CallbackQueryHandler(menu_callback))

    # Chạy polling
    application.run_polling()

if __name__ == "__main__":
    main()

import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.menu import menu, menu_callback_handler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    # ... các handler khác nếu có ...
    app.run_polling()  # Railway sẽ tự giữ process này chạy

if __name__ == "__main__":
    main()

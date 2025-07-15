import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.menu import menu, menu_callback_handler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

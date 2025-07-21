from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu, help_command, menu_callback_handler
app.add_handler(CommandHandler("start", menu))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("reset", reset_command))
app.add_handler(CallbackQueryHandler(menu_callback_handler))
from handlers.text_handlers import all_text_handler
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.bot_data["ADMIN_IDS"] = ADMIN_IDS

    # Lệnh
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))

    # Menu buttons
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Tin nhắn văn bản
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    # KHÔNG DÙNG asyncio.run() nữa
    app.run_polling()

if __name__ == "__main__":
    main()

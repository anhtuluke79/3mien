import os
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from handlers.menu import menu, menu_callback_handler
from ungho import ung_ho_gop_y
from system.admin import admin_menu

TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

def only_command(update, context):
    """Bot không trả lời mọi tin nhắn text tự do."""
    return

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ungho", ung_ho_gop_y))
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    # Không trả lời mọi text tự do
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, only_command))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

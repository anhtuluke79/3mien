import os
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from handlers.menu import menu, menu_callback_handler
from handlers.ungho import ung_ho_gop_y
from system.admin import admin_menu

# ===== Đọc token từ biến môi trường =====
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

def only_command(update, context):
    """Đây là handler 'rỗng' để bot không trả lời tin nhắn thường"""
    return

def main():
    app = Application.builder().token(TOKEN).build()

    # Menu chính
    app.add_handler(CommandHandler("menu", menu))

    # Hướng dẫn
    # from handlers.menu import help_command
    # app.add_handler(CommandHandler("help", help_command))

    # Ủng hộ/góp ý (nếu muốn /ungho riêng)
    app.add_handler(CommandHandler("ungho", ung_ho_gop_y))

    # Menu admin (nếu muốn /admin riêng)
    app.add_handler(CommandHandler("admin", admin_menu))

    # Toàn bộ callback menu
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Đảm bảo không trả lời mọi text thường (chỉ cho phép text khi context đang chờ input đặc biệt)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, only_command))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

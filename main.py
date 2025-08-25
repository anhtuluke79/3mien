
import os
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from handlers.menu import menu, menu_callback_handler
from handlers.input_handler import handle_user_free_input
from system.admin import admin_menu, admin_callback_handler

TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

def main():
    app = Application.builder().token(TOKEN).build()

    # Lệnh gọi menu chính
    app.add_handler(CommandHandler("menu", menu))
    # Lệnh gọi admin menu
    app.add_handler(CommandHandler("admin", admin_menu))
    # Callback cho menu bot (cả người dùng và admin)
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^(?!admin_)"))  # không phải admin_ prefix
    # Callback cho admin (phải đăng ký riêng)
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    # Xử lý nhập tự do (người dùng nhập bất kỳ text nào)
    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_free_input))

    print("🤖 Bot is running... /menu để bắt đầu.")
    app.run_polling()

if __name__ == "__main__":
    main()

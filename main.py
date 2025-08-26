import os
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler
)
from handlers.menu import menu, menu_callback_handler
from system.admin import admin_menu, admin_callback_handler

# Lấy BOT TOKEN từ biến môi trường Railway
TOKEN = os.getenv("BOT_TOKEN")

def main():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN chưa được set trong Railway Variables")

    app = Application.builder().token(TOKEN).build()

    # Đăng ký các lệnh
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_menu))

    # Callback handlers
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^(?!admin_)"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # Railway sẽ tự set PORT, nếu không có thì mặc định 8080
    PORT = int(os.getenv("PORT", 8080))

    print("🤖 Bot is running with webhook...")

    # URL Railway app, thay YOUR-APP-NAME bằng tên project của bạn
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://YOUR-APP-NAME.up.railway.app/{TOKEN}"
    )

if __name__ == "__main__":
    main()

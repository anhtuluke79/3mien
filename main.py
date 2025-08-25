import os
from telegram.ext import Updater, CommandHandler
from handlers.menu import menu, menu_handler

# Lệnh /start
def start(update, context):
    update.message.reply_text("🤖 Xin chào! Đây là bot xổ số.")
    menu(update, context)  # Hiện menu khi start


def main():
    # Lấy token từ biến môi trường Railway
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN chưa được cấu hình trong Railway Variables!")

    # Khởi tạo bot
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Lệnh /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Menu callback
    dispatcher.add_handler(menu_handler)

    # Chạy bot
    port = int(os.environ.get("PORT", 8443))
    updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RAILWAY_STATIC_URL')}/{TOKEN}"
    )
    updater.idle()


if __name__ == "__main__":
    main()

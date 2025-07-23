from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu, menu_callback_handler
# Import thêm các handler command khác nếu muốn (ví dụ help, reset...)

def main():
    # Đặt token vào biến môi trường, hoặc thay trực tiếp cho demo
    import os
    TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    # /menu: mở menu chính
    app.add_handler(CommandHandler("menu", menu))

    # Callback nút bấm menu
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Có thể add thêm các handler message/text, ví dụ:
    # from handlers.menu import handle_text_input
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Khởi chạy bot
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from handlers.menu import menu, help_command, menu_callback_handler
from handlers.text_handlers import all_text_handler

TOKEN = "YOUR_BOT_TOKEN"  # Thay bằng token thật

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Lệnh bắt đầu và trợ giúp
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # Xử lý tương tác menu
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý text bất kỳ (sau khi bấm menu)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    # Chạy bot
    print("Bot is running...")
    await app.run_polling(close_loop=False)  # <- Đừng tự đóng loop nếu đã có loop chạy

# Fix lỗi khi chạy trong môi trường có loop đang chạy
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if str(e).startswith("Cannot close a running event loop"):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise e

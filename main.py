import asyncio
import os
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from handlers.menu import menu, menu_callback_handler, help_command
from handlers.text_handlers import all_text_handler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(',')))

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Lưu admin_ids vào bot_data để dùng ở menu
    app.bot_data["ADMIN_IDS"] = ADMIN_IDS

    # Các lệnh chính
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))

    # Xử lý menu tương tác
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý văn bản khi bot đang chờ đầu vào cụ thể
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    # Chạy bot
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

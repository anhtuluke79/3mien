import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from handlers.menu import (
    menu,
    help_command,
    menu_callback_handler
)

from handlers.text_handlers import all_text_handler

# 🔑 Thay bằng token bot thật của bạn
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 🧭 Lệnh /start và /help
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("help", help_command))

    # 🎛 Xử lý các nút callback từ InlineKeyboard
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # 💬 Xử lý tất cả tin nhắn văn bản không phải là lệnh
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    print("🤖 Bot Telegram đã sẵn sàng!")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())

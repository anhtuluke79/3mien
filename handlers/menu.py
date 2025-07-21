import os
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram import Update

from handlers.menu import (
    menu,
    help_command,
    menu_callback_handler,
    reset_command
)
from handlers.text_handlers import all_text_handler

# Cấu hình logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Lấy token từ biến môi trường
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Biến môi trường BOT_TOKEN chưa được thiết lập.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Lệnh chính
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # Callback từ nút bấm
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý nhập liệu văn bản tự do
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    print("✅ Bot đang chạy...")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise e

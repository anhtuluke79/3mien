import os
import logging

# Bổ sung nest_asyncio để fix lỗi event loop (cần cài pip install nest_asyncio)
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from handlers.menu import (
    menu,
    help_command,
    reset_command,
    phongthuy_command,
    menu_callback_handler
)
from handlers.text_handlers import all_text_handler

# Cấu hình logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Lấy BOT_TOKEN từ biến môi trường
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Biến môi trường BOT_TOKEN chưa được thiết lập.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Các lệnh chính
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("phongthuy", phongthuy_command))

    # Callback menu
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý nhập liệu văn bản (số, ngày, can chi, ...)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    print("🤖 Bot Telegram đã sẵn sàng!")
    await app.run_polling(close_loop=False)  # Sử dụng close_loop=False để không tự đóng event loop

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

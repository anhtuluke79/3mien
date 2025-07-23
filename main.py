import os
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers.menu import (
    menu,
    help_command,
    reset_command,
    phongthuy_command,
    menu_callback_handler,
)
from handlers.text_handlers import all_text_handler

# Thiết lập logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Lấy BOT_TOKEN từ biến môi trường Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Biến môi trường BOT_TOKEN chưa được thiết lập.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Đăng ký handler cho các lệnh
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("phongthuy", phongthuy_command))

    # Callback menu & các nút Inline
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý các message TEXT từ user
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    logger.info("🤖 Bot Telegram đã sẵn sàng! Railway production")
    await app.run_polling()  # KHÔNG cần close_loop=False

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

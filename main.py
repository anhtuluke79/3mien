import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu
from handlers.callbacks import menu_callback_handler
from handlers.input_handler import all_text_handler
from handlers.admin import admin_menu_handler, admin_callback_handler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Chưa thiết lập TELEGRAM_TOKEN!")

async def start(update, context):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_menu_handler))

    # Callback cho admin (riêng pattern các lệnh admin)
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(train_model_db|train_model_lo|capnhat_xsmb|upload_csv_github|main_menu)$"))

    # Callback cho các menu bình thường
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý nhập text theo ngữ cảnh thao tác (không trả lời tự do)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()

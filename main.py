import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.menu import menu_handler
from handlers.callbacks import menu_callback_handler
from handlers.admin import admin_menu_handler, admin_callback_handler
from utils.get_kqxs import get_kqxs  # Hàm lấy kết quả xổ số, xem ở cuối hướng dẫn

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Chưa thiết lập TELEGRAM_TOKEN!")

async def start(update, context):
    await menu_handler(update, context)

async def ketqua_handler(update, context):
    msg = get_kqxs('mb')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mn_handler(update, context):
    msg = get_kqxs('mn')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mt_handler(update, context):
    msg = get_kqxs('mt')
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("admin", admin_menu_handler))
    app.add_handler(CommandHandler("ketqua", ketqua_handler))
    app.add_handler(CommandHandler("mb", ketqua_handler))
    app.add_handler(CommandHandler("mn", mn_handler))
    app.add_handler(CommandHandler("mt", mt_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

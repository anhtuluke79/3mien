from telegram import Update
from telegram.ext import ContextTypes

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chức năng admin đang được phát triển.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Admin callback đang cập nhật.")

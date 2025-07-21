from telegram import Update
from telegram.ext import ContextTypes

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chức năng admin đang được phát triển.")

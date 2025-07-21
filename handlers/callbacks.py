from telegram import Update
from telegram.ext import ContextTypes

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chức năng đang được cập nhật.")

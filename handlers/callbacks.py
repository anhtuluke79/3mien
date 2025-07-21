from telegram import Update
from telegram.ext import ContextTypes

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Xử lý các callback từ menu (nếu chưa có chức năng cụ thể, trả về như dưới)
    await update.callback_query.answer("Tính năng đang cập nhật.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Xử lý các callback admin (nếu có)
    await update.callback_query.answer("Admin callback đang cập nhật.")

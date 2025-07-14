from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from user_manage import is_super_admin
from logic_xsmb import *
import os

async def admin_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("🧠 Train & Lưu model", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬆️ Upload model lên Github", callback_data="admin_upload_model")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên Github", callback_data="admin_upload_csv")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

async def backup_restore_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📤 Backup dữ liệu", callback_data="backup_data")],
        [InlineKeyboardButton("📥 Restore dữ liệu", callback_data="restore_data")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("🗂 Backup / Restore dữ liệu:", reply_markup=InlineKeyboardMarkup(keyboard))

# (Các callback admin khác như crawl, train, backup... có thể để chung trong menu_callback_handler
# hoặc tách riêng thành hàm nếu muốn modular hơn)

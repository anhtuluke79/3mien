import os
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import utils.thongkemb as tk
import utils.ai_rf as ai_rf

# ========== ADMIN IDS ==========
ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(","))

# ========== KEYBOARD ==========
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Xem log sử dụng", callback_data="admin_view_log")],
        [InlineKeyboardButton("📥 Crawl XSMB (chọn số ngày)", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên GitHub", callback_data="admin_upload_github")],
        [InlineKeyboardButton("📤 Tải file xsmb.csv", callback_data="admin_download_csv")],
        [InlineKeyboardButton("🤖 Train AI Random Forest", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_crawl_days_keyboard():
    keyboard = [
        [InlineKeyboardButton("10 ngày", callback_data="admin_crawl_days_10"),
         InlineKeyboardButton("30 ngày", callback_data="admin_crawl_days_30")],
        [InlineKeyboardButton("60 ngày", callback_data="admin_crawl_days_60"),
         InlineKeyboardButton("100 ngày", callback_data="admin_crawl_days_100")],
        [InlineKeyboardButton("⬅️ Quản trị", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_rf_ngay_keyboard():
    keyboard = [
        [InlineKeyboardButton("7 ngày", callback_data="ai_rf_N_7"),
         InlineKeyboardButton("14 ngày", callback_data="ai_rf_N_14")],
        [InlineKeyboardButton("21 ngày", callback_data="ai_rf_N_21"),
         InlineKeyboardButton("28 ngày", callback_data="ai_rf_N_28")],
        [InlineKeyboardButton("⬅️ Quản trị", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== LOG DECORATOR ==========
def log_user_action(action):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            with open("user_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{user.id}|{user.username}|{user.first_name}|{action}\n")
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# ========== ADMIN MENU ==========
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "🛡️ *Menu quản trị* (chỉ admin):\n- Xem log\n- Crawl XSMB\n- Upload lên GitHub\n- Train AI Random Forest\n- ... (nâng cấp sau)"
    if user_id not in ADMIN_IDS:
        text = "⛔ Bạn không có quyền truy cập menu quản trị!"
        if getattr(update, "message", None):
            await update.message.reply_text(text, parse_mode="Markdown")
        elif getattr(update, "callback_query", None):
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        return

    if getattr(update, "message", None):
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())
    elif getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())

# ========== ASYNC SUPPORT ==========
async def do_upload_and_send(context, chat_id):
    from utils.upload_github import upload_file_to_github
    github_token = os.getenv("GITHUB_TOKEN")
    try:
        await asyncio.to_thread(
           

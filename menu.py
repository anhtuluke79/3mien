# handlers/menu.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.utils import is_admin

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("🔢 Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
        keyboard.append([InlineKeyboardButton("🗂 Backup/Restore", callback_data="backup_restore_menu")])
    text = "🔹 Chọn chức năng:"
    # Hỗ trợ cả /start, /menu, callback menu
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    # Chỉ demo cho menu chính, các menu con sẽ thêm sau
    if data == "main_menu":
        await menu(update, context)
    else:
        await query.edit_message_text("❗️Chức năng này đang phát triển!")

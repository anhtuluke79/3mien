from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    user_id = update.effective_user.id if update.effective_user else None

    keyboard = [
        [InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🤖 Dự đoán MB", callback_data="ai_menu")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang")],
        [InlineKeyboardButton("🔁 Đảo số", callback_data="daoso")],
        [InlineKeyboardButton("💗 Ủng hộ/Đóng góp", callback_data="ungho_menu")],
    ]
    if user_id in ADMIN_IDS:
        keyboard.append(
            [InlineKeyboardButton("🛠️ Quản trị/Admin", callback_data="admin_menu")]
        )

    welcome = (
        "✨ <b>Chào mừng đến với XosoBot!</b>\n"
        "Hãy chọn chức năng bên dưới 👇"
    )
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(
            welcome,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.callback_query.message.reply_text(
            welcome,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

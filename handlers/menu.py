from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

MY_ID = 892780229  # <-- sửa thành Telegram user_id của bạn
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Chỉ trả lời nhóm hoặc nhắn riêng với chính bạn
    if chat.type == "private" and user.id != MY_ID:
        return

    user_id = user.id if user else None

    keyboard = [
        [InlineKeyboardButton("🤖 Dự đoán MB", callback_data="ai_menu")],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("🔁 Đảo số", callback_data="daoso"),
        ],
        [InlineKeyboardButton("💗 Ủng hộ/Đóng góp", callback_data="ungho_menu")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛠️ Quản trị/Admin", callback_data="admin_menu")])

    welcome = (
        "✨ <b>Chào mừng đến với XosoBot!</b>\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
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

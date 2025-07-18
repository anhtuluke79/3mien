# handlers/menu.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None

    keyboard = [
        [InlineKeyboardButton("🤖 Dự đoán MB", callback_data="ai_menu")],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("🔁 Đảo số", callback_data="daoso"),
        ],
        [InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("💗 Ủng hộ/Đóng góp", callback_data="ungho_menu")],
    ]

    # Chỉ hiện admin cho ADMIN_IDS
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("🛠️ Quản trị/Admin", callback_data="admin_menu"),
        ])

    welcome = (
        "✨ <b>Chào mừng bạn đến với Thần tài!</b>\n"
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

async def ungho_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💸 Ủng hộ", callback_data="ungho_ck"),
            InlineKeyboardButton("✍️ Đóng góp ý kiến", callback_data="donggop_ykien"),
        ],
        [
            InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu"),
        ]
    ]
    await update.callback_query.message.reply_text(
        "<b>Bạn muốn ủng hộ hoặc đóng góp gì?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def ungho_ck_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💗 <b>Cảm ơn bạn đã quan tâm và ủng hộ XosoBot!</b>\n\n"
        "Bạn có thể chuyển khoản qua ngân hàng:\n"
        "<b>Ngân hàng:</b> Vietcombank\n"
        "<b>Tên:</b> TRUONG ANH TU\n"
        "<b>Số TK:</b> 0071003914986\n"
        "Nội dung: <code>Ung ho phat trien - tên nick telegram của bạn</code>\n\n"
        "Mỗi sự đóng góp của bạn là động lực lớn để phát triển bot miễn phí và chất lượng hơn! 🙏"
    )
    await update.callback_query.message.reply_text(text, parse_mode="HTML")

async def donggop_ykien_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wait_for_feedback'] = True
    text = (
        "✍️ <b>Hãy nhập góp ý hoặc ý tưởng của bạn!</b>\n"
        "Bot sẽ gửi trực tiếp tới admin. Xin cảm ơn! 💡"
    )
    await update.callback_query.message.reply_text(text, parse_mode="HTML")

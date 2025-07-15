from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None

    keyboard = [
        [
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("🔁 Đảo số", callback_data="daoso"),
        ],
        [
            InlineKeyboardButton("📖 Hướng dẫn", callback_data="huongdan"),
        ]
    ]

    # Chỉ hiện nút admin nếu là admin
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("⚙️ Train lại AI", callback_data="train_model"),
            InlineKeyboardButton("🛠️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
        ])

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

# Nếu bạn muốn thêm hướng dẫn chi tiết khi bấm "📖 Hướng dẫn"
async def huongdan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>📖 Hướng dẫn sử dụng XosoBot</b>\n\n"
        "• <b>Phong thủy ngày</b>: tra cứu số phong thủy, ngũ hành theo ngày hoặc can chi.\n"
        "• <b>Ghép xiên</b>: nhập các số cần ghép thành bộ xiên 2, 3, 4...\n"
        "• <b>Ghép càng</b>: nhập số 2 hoặc 3 chữ số, nhập càng, bot tự ghép đầu càng.\n"
        "• <b>Đảo số</b>: nhập số bất kỳ (3 hoặc 4 chữ số), bot trả toàn bộ các hoán vị.\n"
        "\n"
        "Nếu có thắc mắc hoặc góp ý, hãy liên hệ admin.\n"
        "Chúc bạn may mắn! 🍀"
    )
    await update.callback_query.message.reply_text(text, parse_mode="HTML")

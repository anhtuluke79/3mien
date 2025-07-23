import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_ungho_text():
    return (
        "💖 *ỦNG HỘ & GÓP Ý CHO BOT*\n"
        "Cảm ơn bạn đã sử dụng bot! Nếu thấy hữu ích, bạn có thể ủng hộ để mình duy trì và phát triển thêm tính năng.\n\n"
        "🔗 *Chuyển khoản Vietcombank:*\n"
        "`0071003914986`\n"
        "_TRUONG ANH TU_\n\n"
        "Hoặc quét mã QR bên dưới.\n\n"
        "🌟 *Góp ý/đề xuất tính năng*: nhắn trực tiếp qua Telegram hoặc email: tutruong19790519@gmail.com\n"
        "Rất mong nhận được ý kiến của bạn! 😊"
    )

def get_ungho_keyboard():
    # Có thể thêm nút liên hệ, trở về menu, v.v. nếu muốn
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]
    ])

def get_qr_image_path():
    # Đường dẫn ảnh mã QR (cùng thư mục root với main.py hoặc ghi đường dẫn tuyệt đối)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "qr_ung_ho.png")

# ==================== HANDLER TELEGRAM =====================
async def ung_ho_gop_y(update, context):
    text = get_ungho_text()
    qr_path = get_qr_image_path()
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_ungho_keyboard()
        )
    elif hasattr(update, "message") and update.message:
        await update.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_ungho_keyboard()
        )

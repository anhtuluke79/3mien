from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard():
    keyboard = [
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="menu")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "📋 Chọn chức năng:"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟣 HƯỚNG DẪN SỬ DỤNG:\n"
        "- Chọn 'Ghép xiên' để nhập số và chọn loại xiên.\n"
        "- Chọn 'Ghép càng/Đảo số' để ghép càng hoặc đảo số cho dàn đề/lô.\n"
        "- Chọn 'Phong thủy số' để tra cứu số hợp theo ngày hoặc can chi.\n"
        "- Gõ /menu để hiện lại menu chức năng.\n"
        "- Gõ /reset để xóa trạng thái và bắt đầu lại.",
        reply_markup=get_back_reset_keyboard()
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 Đã reset trạng thái. Bạn có thể bắt đầu lại bằng lệnh /menu hoặc chọn lại chức năng!",
        reply_markup=get_menu_keyboard()
    )

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🔮 PHONG THỦY SỐ\nBạn muốn tra cứu số hợp theo:\n- Ngày dương lịch (VD: 2024-07-21 hoặc 21-07)\n- Can chi (VD: Giáp Tý, Ất Mão, ...)\n\nNhập 1 trong 2 tuỳ chọn phía trên:"
    await update.message.reply_text(text, reply_markup=get_back_reset_keyboard())
    context.user_data["wait_phongthuy_ngay_duong"] = True
    context.user_data["wait_phongthuy_ngay_canchi"] = True

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    # Không clear user_data nếu người dùng nhấn Quay lại menu!
    if data == "menu":
        await menu(update, context)
        return
    context.user_data.clear()
    if data == "ghep_xien":
        await query.edit_message_text(
            "🔢 Nhập dàn số (cách nhau bằng dấu cách, xuống dòng, hoặc dấu phẩy):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_for_xien_input'] = 2  # mặc định xiên 2, có thể hỏi lại nếu muốn chọn loại
    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "🎯 Nhập dàn đề hoặc lô (2 hoặc 3 chữ số, cách nhau bằng dấu cách):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_cang3d_numbers'] = True
    elif data == "phongthuy":
        await phongthuy_command(update, context)
    elif data == "huongdan":
        await help_command(update, context)
    elif data == "reset":
        await reset_command(update, context)
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard())

# ĐẢM BẢO EXPORT ĐẦY ĐỦ
__all__ = [
    "menu",
    "help_command",
    "reset_command",
    "phongthuy_command",
    "menu_callback_handler",
    "get_menu_keyboard",
    "get_back_reset_keyboard"
]

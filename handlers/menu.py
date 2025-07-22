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

def get_xien_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Xiên 2", callback_data="xien_2"),
            InlineKeyboardButton("Xiên 3", callback_data="xien_3"),
            InlineKeyboardButton("Xiên 4", callback_data="xien_4")
        ],
        [
            InlineKeyboardButton("⬅️ Quay lại", callback_data="back_to_menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Quay lại menu", callback_data="back_to_menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
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
    text = (
        "🟣 HƯỚNG DẪN SỬ DỤNG:\n"
        "- Chọn 'Ghép xiên' để nhập số và chọn loại xiên.\n"
        "- Chọn 'Ghép càng/Đảo số' để ghép càng hoặc đảo số cho dàn đề/lô.\n"
        "- Chọn 'Phong thủy số' để tra cứu số hợp theo ngày hoặc can chi.\n"
        "- Gõ /menu để hiện lại menu chức năng.\n"
        "- Gõ /reset để xóa trạng thái và bắt đầu lại."
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=get_back_reset_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_back_reset_keyboard())

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🔄 Đã reset trạng thái. Bạn có thể bắt đầu lại bằng lệnh /menu hoặc chọn lại chức năng!"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard())

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c

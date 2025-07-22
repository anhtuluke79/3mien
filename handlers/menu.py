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
            InlineKeyboardButton("Xiên 2", callback_data="xien2"),
            InlineKeyboardButton("Xiên 3", callback_data="xien3"),
            InlineKeyboardButton("Xiên 4", callback_data="xien4")
        ],
        [
            InlineKeyboardButton("⬅️ Quay lại", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard():
    keyboard = [
        [InlineKeyboardButton("⬅️ Quay lại", callback_data="menu")],
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
    text = (
        "🟣 *HƯỚNG DẪN SỬ DỤNG:*\n"
        "- *Ghép xiên*: Nhập số, chọn loại xiên 2-3-4.\n"
        "- *Ghép càng/Đảo số*: Ghép càng cho dàn lô/đề, đảo số, đảo 2-6 số.\n"
        "- *Phong thủy số*: Tra số hợp theo ngày hoặc can chi.\n"
        "- Gõ /menu để trở lại menu, /reset để xóa trạng thái và bắt đầu lại."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🔄 Đã reset trạng thái. Gõ /menu hoặc nhấn để bắt đầu lại."
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard())

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "🔮 *PHONG THỦY SỐ*\n"
        "Bạn muốn tra cứu số hợp theo:\n"
        "- Ngày dương lịch (VD: 2024-07-21 hoặc 21-07)\n"
        "- Can chi (VD: Giáp Tý, Ất Mão, ...)\n"
        "Nhập ngày dương hoặc can chi:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard())
    context.user_data["wait_phongthuy"] = True

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    context.user_data.clear()
    if data == "menu":
        await menu(update, context)
    elif data == "ghep_xien":
        await query.edit_message_text("🔢 Nhập dàn số (cách nhau bởi dấu cách, dấu phẩy hoặc xuống dòng):", reply_markup=get_xien_keyboard())
        context.user_data['wait_for_xien_input'] = None
    elif data in ["xien2", "xien3", "xien4"]:
        n = int(data[-1])
        context.user_data['wait_for_xien_input'] = n
        await query.edit_message_text(f"🔢 Nhập dàn số để ghép xiên {n} (cách nhau bởi dấu cách, dấu phẩy hoặc xuống dòng):", reply_markup=get_back_reset_keyboard())
    elif data == "ghep_cang_dao":
        await query.edit_message_text("🎯 Nhập dàn đề/lô (2 hoặc 3 chữ số, cách nhau bằng dấu cách):", reply_markup=get_back_reset_keyboard())
        context.user_data['wait_cang3d_numbers'] = True
    elif data == "phongthuy":
        await phongthuy_command(update, context)
    elif data == "huongdan":
        await help_command(update, context)
    elif data == "reset":
        await reset_command(update, context)
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard())

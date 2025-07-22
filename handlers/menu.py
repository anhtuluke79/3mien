from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ===== MENU PHỤ =====
def get_xien_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Xiên 2", callback_data="xien_2"),
            InlineKeyboardButton("Xiên 3", callback_data="xien_3"),
            InlineKeyboardButton("Xiên 4", callback_data="xien_4"),
        ],
        [
            InlineKeyboardButton("⬅️ Quay lại menu", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cang_dao_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Ghép càng 3D", callback_data="cang_3d"),
            InlineKeyboardButton("Ghép càng 4D", callback_data="cang_4d"),
            InlineKeyboardButton("Đảo số", callback_data="dao_so"),
        ],
        [
            InlineKeyboardButton("⬅️ Quay lại menu", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Quay lại menu", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== MENU CHÍNH =====
def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== CÁC LỆNH XỬ LÝ MENU =====
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
        "- Gõ /reset để xóa trạng thái và bắt đầu lại."
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 Đã reset trạng thái. Bạn có thể bắt đầu lại bằng lệnh /menu hoặc chọn lại chức năng!",
        reply_markup=get_menu_keyboard()
    )

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "🔮 PHONG THỦY SỐ\nBạn muốn tra cứu số hợp theo:\n"
        "- Ngày dương lịch (VD: 2024-07-21 hoặc 21-07)\n"
        "- Can chi (VD: Giáp Tý, Ất Mão, ...)\n\n"
        "Nhập 1 trong 2 tuỳ chọn phía trên:"
    )
    await update.message.reply_text(text, reply_markup=get_back_reset_keyboard())
    context.user_data["wait_phongthuy_ngay_duong"] = True
    context.user_data["wait_phongthuy_ngay_canchi"] = True

# ===== XỬ LÝ CALLBACK MENU =====
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    context.user_data.clear()

    if data == "ghep_xien":
        await query.edit_message_text(
            "🔢 Chọn loại xiên:",
            reply_markup=get_xien_keyboard()
        )
    elif data.startswith("xien_"):
        do_dai = int(data.split("_")[1])
        await query.edit_message_text(
            f"🔢 Nhập dàn số để ghép xiên {do_dai} (cách nhau bằng dấu cách, xuống dòng, hoặc dấu phẩy):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_for_xien_input'] = do_dai

    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "🎯 Chọn chức năng:",
            reply_markup=get_cang_dao_keyboard()
        )
    elif data == "cang_3d":
        await query.edit_message_text(
            "📥 Nhập dàn số 2 chữ số (VD: 12 23 45):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_cang3d_numbers'] = True
    elif data == "cang_4d":
        await query.edit_message_text(
            "📥 Nhập dàn số 3 chữ số (VD: 123 456 789):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_cang4d_numbers'] = True
    elif data == "dao_so":
        await query.edit_message_text(
            "🔄 Nhập số muốn đảo (tối đa 6 số):",
            reply_markup=get_back_reset_keyboard()
        )
        context.user_data['wait_for_dao_input'] = True

    elif data == "phongthuy":
        await phongthuy_command(update, context)
    elif data == "huongdan":
        if query.message:
            await query.edit_message_text(
                "🟣 HƯỚNG DẪN SỬ DỤNG:\n"
                "- Chọn 'Ghép xiên' để nhập số và chọn loại xiên.\n"
                "- Chọn 'Ghép càng/Đảo số' để ghép càng hoặc đảo số cho dàn đề/lô.\n"
                "- Chọn 'Phong thủy số' để tra cứu số hợp theo ngày hoặc can chi.\n"
                "- Gõ /menu để hiện lại menu chức năng.\n"
                "- Gõ /reset để xóa trạng thái và bắt đầu lại.",
                reply_markup=get_back_reset_keyboard()
            )
    elif data == "reset":
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 Đã reset trạng thái. Bạn có thể bắt đầu lại bằng lệnh /menu hoặc chọn lại chức năng!",
            reply_markup=get_menu_keyboard()
        )
    elif data == "menu":
        await query.edit_message_text(
            "📋 Chọn chức năng:",
            reply_markup=get_menu_keyboard()
        )
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard())

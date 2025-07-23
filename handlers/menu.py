from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên (Tổ hợp số)", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số (Ngày/Can chi)", callback_data="phongthuy")],
        [InlineKeyboardButton("💖 Ủng hộ / Góp ý", callback_data="ung_ho_gop_y")],  # Nút mới
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_xien_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
            InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
            InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")
        ],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cang_dao_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d")],
        [InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d")],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard(menu_callback="menu"):
    keyboard = [
        [InlineKeyboardButton("⬅️ Quay lại", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🟣 *HƯỚNG DẪN NHANH:*\n"
        "— *Ghép xiên*: Nhập dàn số bất kỳ, chọn loại xiên 2-3-4, bot sẽ trả mọi tổ hợp xiên.\n"
        "— *Ghép càng/Đảo số*: Nhập dàn số 2 hoặc 3 chữ số, nhập càng muốn ghép, hoặc đảo số từ 2-6 chữ số.\n"
        "— *Phong thủy số*: Tra cứu số hợp theo ngày dương hoặc can chi (VD: 2025-07-23 hoặc Giáp Tý).\n"
        "— Luôn có nút menu trở lại, reset trạng thái, hoặc gõ /menu để quay về ban đầu."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🔄 *Đã reset trạng thái.*\nQuay lại menu chính để bắt đầu mới!"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "🔮 *PHONG THỦY SỐ*\n"
        "- Nhập ngày dương (VD: 2025-07-23 hoặc 23-07)\n"
        "- Hoặc nhập can chi (VD: Giáp Tý, Ất Mão)\n"
        "— Kết quả gồm can, mệnh, số hạp."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("menu"))
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("menu"))
    context.user_data["wait_phongthuy"] = True

async def ung_ho_gop_y(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💖 *ỦNG HỘ & GÓP Ý CHO BOT*\n"
        "Cảm ơn bạn đã sử dụng bot! Nếu thấy hữu ích, bạn có thể ủng hộ để mình duy trì và phát triển thêm tính năng.\n\n"
        "🔗 *Chuyển khoản Vietcombank:*\n"
        "`0071003914986`\n"
        "_TRUONG ANH TU_\n\n"
        "Hoặc quét mã QR bên dưới.\n\n"
        "🌟 *Góp ý/đề xuất tính năng*: nhắn trực tiếp qua Telegram hoặc email: tutruong19790519@gmail.com\n"
        "Rất mong nhận được ý kiến của bạn! 😊"
    )
    qr_path = "qr_ung_ho.png"  # Đảm bảo file QR ở đúng vị trí
    await update.callback_query.message.reply_photo(
        photo=open(qr_path, "rb"),
        caption=text,
        parse_mode="Markdown",
        reply_markup=get_menu_keyboard()
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    context.user_data.clear()
    if data == "menu":
        await menu(update, context)
    elif data == "ghep_xien":
        await query.edit_message_text(
            "*🔢 Ghép xiên* — Chọn loại xiên muốn ghép:",
            reply_markup=get_xien_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['wait_for_xien_input'] = None
    elif data in ["xien2", "xien3", "xien4"]:
        n = int(data[-1])
        context.user_data['wait_for_xien_input'] = n
        await query.edit_message_text(
            f"*🔢 Ghép xiên {n}* — Nhập dàn số cách nhau bằng dấu cách, phẩy hoặc xuống dòng:",
            reply_markup=get_back_reset_keyboard("ghep_xien"), parse_mode="Markdown"
        )
    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "*🎯 Ghép càng/Đảo số* — Chọn chức năng bên dưới:",
            reply_markup=get_cang_dao_keyboard(), parse_mode="Markdown"
        )
    elif data == "ghep_cang3d":
        await query.edit_message_text(
            "Nhập dàn số 2 chữ số (VD: 12 34 56):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_cang3d_numbers'] = True
    elif data == "ghep_cang4d":
        await query.edit_message_text(
            "Nhập dàn số 3 chữ số (VD: 123 456 789):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_cang4d_numbers'] = True
    elif data == "dao_so":
        await query.edit_message_text(
            "Nhập 1 số bất kỳ (2-6 chữ số, VD: 1234):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_for_dao_input'] = True
    elif data == "phongthuy":
        await phongthuy_command(update, context)
    elif data == "huongdan":
        await help_command(update, context)
    elif data == "reset":
        await reset_command(update, context)
    elif data == "ung_ho_gop_y":
        await ung_ho_gop_y(update, context)
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard())

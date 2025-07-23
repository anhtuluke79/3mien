from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Thêm danh sách admin ID (sửa lại theo bạn)
ADMIN_IDS = [123456789, 987654321]  # Thay bằng ID admin thực tế

def get_menu_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên (Tổ hợp số)", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số (Ngày/Can chi)", callback_data="phongthuy")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("💬 Góp ý & Phản hồi", callback_data="gopy")],
        [InlineKeyboardButton("☕ Ủng hộ tác giả", callback_data="ung_ho")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị Admin", callback_data="admin_tool")])
    keyboard.append([InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset")])
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

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Thống kê truy cập", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Gửi Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🗂 Lịch sử góp ý", callback_data="admin_gopy")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id if update.effective_user else None
    is_admin = user_id in ADMIN_IDS
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(is_admin), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(is_admin), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    is_admin = user_id in ADMIN_IDS
    text = (
        "🟣 *HƯỚNG DẪN NHANH:*\n"
        "— *Ghép xiên*: Nhập dàn số bất kỳ, chọn loại xiên 2-3-4, bot sẽ trả mọi tổ hợp xiên.\n"
        "— *Ghép càng/Đảo số*: Nhập dàn số 2 hoặc 3 chữ số, nhập càng muốn ghép, hoặc đảo số từ 2-6 chữ số.\n"
        "— *Phong thủy số*: Tra cứu số hợp theo ngày dương hoặc can chi (VD: 2025-07-23 hoặc Giáp Tý).\n"
        "— Luôn có nút menu trở lại, reset trạng thái, hoặc gõ /menu để quay về ban đầu."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard(is_admin))
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard(is_admin))

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id if update.effective_user else None
    is_admin = user_id in ADMIN_IDS
    text = "🔄 *Đã reset trạng thái.*\nQuay lại menu chính để bắt đầu mới!"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(is_admin), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(is_admin), parse_mode="Markdown")

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

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id if update.effective_user else None
    is_admin = user_id in ADMIN_IDS
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
    elif data == "gopy":
        await query.edit_message_text(
            "💬 *Góp ý & Phản hồi*\nVui lòng nhập nội dung bạn muốn góp ý/nhắn nhủ cho tác giả:",
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )
        context.user_data["wait_for_gopy"] = True
    elif data == "ung_ho":
        await query.edit_message_text(
            "☕ *ỦNG HỘ TÁC GIẢ*\nNếu bạn thấy bot hữu ích, có thể ủng hộ qua Viecombank: *0071003914986*"
            "\nHoặc liên hệ trực tiếp: @anhtuluke",
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )
    elif data == "admin_tool":
        if not is_admin:
            await query.edit_message_text("❌ Bạn không có quyền admin.", reply_markup=get_menu_keyboard(False))
        else:
            await query.edit_message_text(
                "⚙️ *Admin Tool*\nCác chức năng dành riêng cho admin:",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )
    elif data == "reset":
        await reset_command(update, context)
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(is_admin))

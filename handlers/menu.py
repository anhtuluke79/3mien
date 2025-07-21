from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Menu chính
def get_main_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy_menu")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset_state")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    await update.message.reply_text("📋 Chọn chức năng:", reply_markup=keyboard)

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Hướng dẫn sử dụng bot:\n"
        "- Chọn chức năng từ menu\n"
        "- Hỗ trợ ghép xiên, đảo số, càng 3D/4D, phong thủy số\n"
        "- Gõ /reset để xóa trạng thái đang nhập\n"
        "- Gõ /phongthuy để tra nhanh phong thủy số\n"
        "- Mọi vấn đề vui lòng liên hệ admin."
    )

# /reset
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔄 Đã reset trạng thái. Gõ /start để quay lại menu.")

# /phongthuy
async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔢 Theo ngày dương", callback_data="phongthuy_ngay_duong")],
        [InlineKeyboardButton("📝 Theo can chi", callback_data="phongthuy_ngay_canchi")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
    ]
    await update.message.reply_text(
        "🔮 Chọn kiểu tra phong thủy số:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback menu
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data

    if query.data == "main_menu":
        keyboard = get_main_menu_keyboard(query.from_user.id)
        await query.edit_message_text("📋 Chọn chức năng:", reply_markup=keyboard)
        return

    if query.data == "menu_ghepxien":
        keyboard = [
            [InlineKeyboardButton("2 số", callback_data="xien2"),
             InlineKeyboardButton("3 số", callback_data="xien3"),
             InlineKeyboardButton("4 số", callback_data="xien4")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")],
            [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset_state")]
        ]
        await query.edit_message_text("📌 Chọn độ dài xiên muốn tạo:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("xien"):
        do_dai = int(query.data[-1])
        user_data["wait_for_xien_input"] = do_dai
        await query.edit_message_text(f"📥 Nhập các số để ghép xiên {do_dai}:")
        return

    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Càng 3D", callback_data="cang3d"),
             InlineKeyboardButton("Càng 4D", callback_data="cang4d")],
            [InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")],
            [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset_state")]
        ]
        await query.edit_message_text("📌 Chọn loại thao tác:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cang3d":
        user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy 2 số để ghép càng 3D:")
        return

    if query.data == "cang4d":
        user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy 3 số để ghép càng 4D:")
        return

    if query.data == "daoso":
        user_data["wait_for_dao_input"] = True
        await query.edit_message_text("📥 Nhập một số (2-6 chữ số) để đảo:")
        return

    # PHONG THỦY MENU
    if query.data == "phongthuy_menu":
        keyboard = [
            [InlineKeyboardButton("🔢 Theo ngày dương", callback_data="phongthuy_ngay_duong")],
            [InlineKeyboardButton("📝 Theo can chi", callback_data="phongthuy_ngay_canchi")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🔮 Chọn kiểu tra phong thủy số:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "phongthuy_ngay_duong":
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_duong'] = True
        await query.edit_message_text("📅 Nhập ngày dương (YYYY-MM-DD, DD-MM, hoặc YYYY/MM/DD):")
        return

    if query.data == "phongthuy_ngay_canchi":
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_canchi'] = True
        await query.edit_message_text("📜 Nhập can chi (ví dụ: Giáp Tý, ất mão, ...):")
        return

    if query.data == "help":
        await help_command(update, context)
        return

    if query.data == "reset_state":
        context.user_data.clear()
        keyboard = get_main_menu_keyboard(query.from_user.id)
        await query.edit_message_text("🔄 Đã reset trạng thái. Quay về Menu chính:", reply_markup=keyboard)
        return

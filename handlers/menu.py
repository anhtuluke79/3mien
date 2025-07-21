from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from utils.utils import is_admin, get_main_menu_keyboard

# /start command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = get_main_menu_keyboard(is_admin(user.id))
    await update.message.reply_text("📋 Chọn một chức năng bên dưới:", reply_markup=InlineKeyboardMarkup(keyboard))

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Hướng dẫn sử dụng bot:*\n\n"
        "/start - Hiển thị menu chính\n"
        "/help - Hướng dẫn sử dụng\n"
        "/reset - Xoá trạng thái người dùng\n\n"
        "*Các chức năng:* \n"
        "• Tạo xiên (ghép số)\n"
        "• Đảo số\n"
        "• Ghép càng 3D/4D\n"
        "• Phong thuỷ, chốt số\n"
    )
    await update.message.reply_markdown_v2(help_text)

# /reset command
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔄 Đã xoá trạng thái người dùng.")

# Callback handler cho inline menu
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data = context.user_data

    if query.data == "main_menu":
        keyboard = get_main_menu_keyboard(is_admin(query.from_user.id))
        await query.edit_message_text("📋 Quay lại menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))
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

    if query.data == "xien2":
        user_data["wait_for_xien_input"] = 2
        await query.edit_message_text("📥 Nhập danh sách số để ghép xiên 2:")
        return

    if query.data == "xien3":
        user_data["wait_for_xien_input"] = 3
        await query.edit_message_text("📥 Nhập danh sách số để ghép xiên 3:")
        return

    if query.data == "xien4":
        user_data["wait_for_xien_input"] = 4
        await query.edit_message_text("📥 Nhập danh sách số để ghép xiên 4:")
        return

    if query.data == "cang3d":
        user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy số 2 chữ số để ghép với càng (3D):")
        return

    if query.data == "cang4d":
        user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy số 3 chữ số để ghép với càng (4D):")
        return

    if query.data == "daoso":
        user_data["wait_for_daoso_input"] = True
        await query.edit_message_text("📥 Nhập danh sách số để đảo thứ tự:")
        return

    if query.data == "reset_state":
        user_data.clear()
        await query.edit_message_text("🔄 Đã xoá toàn bộ trạng thái người dùng.")
        return

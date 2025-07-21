from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.utils import is_admin, get_main_menu_keyboard

# Lệnh /start hoặc /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = get_main_menu_keyboard(user_id, context.bot_data.get("ADMIN_IDS", []))

    if update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=keyboard)

# Lệnh /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Hướng dẫn sử dụng bot*\n\n"
        "🔸 Chọn chức năng từ menu:\n"
        "➕ Ghép xiên: nhập nhiều số để bot ghép thành xiên 2, 3, 4\n"
        "🎯 Đảo số: nhập 1 số từ 2 đến 6 chữ số, bot sẽ đảo ra các hoán vị\n"
        "🔄 Reset trạng thái: xóa trạng thái nhập liệu nếu bạn muốn làm lại\n\n"
        "💬 Nếu bot không phản hồi, hãy nhập lại bằng cách nhấn Reset hoặc /menu"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Xử lý các callback menu
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # === Reset trạng thái
    if query.data == "reset_state":
        context.user_data.clear()
        await query.edit_message_text("✅ Trạng thái đã được reset!")
        return

    # === Xiên menu
    if query.data == "menu_ghepxien":
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="xi2"),
             InlineKeyboardButton("Xiên 3", callback_data="xi3"),
             InlineKeyboardButton("Xiên 4", callback_data="xi4")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")],
            [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset_state")]
        ]
        await query.edit_message_text("Chọn loại xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data in ["xi2", "xi3", "xi4"]:
        do_dai = int(query.data[-1])
        context.user_data['wait_for_xien_input'] = do_dai
        await query.edit_message_text(f"Nhập dãy số để ghép xiên {do_dai} (cách nhau dấu cách hoặc phẩy):")
        return

    # === Ghép càng / Đảo số
    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")],
            [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset_state")]
        ]
        await query.edit_message_text("Chọn thao tác:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "daoso":
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text("📥 Nhập một số từ 2 đến 6 chữ số để đảo:")
        return

    # === Quay lại menu chính
    if query.data == "main_menu":
        await menu(update, context)
        return

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.utils import is_admin, get_main_menu_keyboard

# Menu chính
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = get_main_menu_keyboard(user_id, context.bot_data.get("ADMIN_IDS", []))
    
    if update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=keyboard)

# Callback menu
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_ghepxien":
        context.user_data.clear()
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="xi2"),
             InlineKeyboardButton("Xiên 3", callback_data="xi3"),
             InlineKeyboardButton("Xiên 4", callback_data="xi4")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data in ["xi2", "xi3", "xi4"]:
        do_dai = int(query.data[-1])
        context.user_data['wait_for_xien_input'] = do_dai
        await query.edit_message_text(f"Nhập dãy số để ghép xiên {do_dai} (cách nhau dấu cách hoặc phẩy):")
        return

    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại thao tác:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "daoso":
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text("Nhập một số (từ 2 đến 6 chữ số) để đảo:")
        return

    if query.data == "main_menu":
        await menu(update, context)
        return

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="ghep_xien")],
        [InlineKeyboardButton("🔁 Đảo số", callback_data="dao_so")],
        [InlineKeyboardButton("🎯 Ghép càng 3D", callback_data="cang3d")],
        [InlineKeyboardButton("🎯 Ghép càng 4D", callback_data="cang4d")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔘 Chọn chức năng:", reply_markup=reply_markup)

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_data = context.user_data

    if data == "ghep_xien":
        user_data["wait_for_xien_input"] = 2
        await query.edit_message_text("📥 Nhập các số để ghép xiên 2:")
    elif data == "dao_so":
        user_data["wait_for_dao_input"] = True
        await query.edit_message_text("📥 Nhập các số muốn đảo:")
    elif data == "cang3d":
        user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text("📥 Nhập dàn 2 số để ghép với càng:")
    elif data == "cang4d":
        user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text("📥 Nhập dàn 3 số để ghép với càng:")
    elif data == "help":
        await help_command(update, context)
    elif data == "reset":
        await reset_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("❓ Hướng dẫn sử dụng bot:\n- /start để bắt đầu\n- Chọn các chức năng qua menu")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text("🔄 Đã reset trạng thái. Gõ /start để bắt đầu lại.")

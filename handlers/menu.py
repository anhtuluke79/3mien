from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.utils import is_admin, get_main_menu_keyboard


# /start hoặc "Quay lại menu chính"
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = get_main_menu_keyboard(user.id)
    await update.message.reply_text("📋 Menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))


# Callback khi chọn nút trong menu
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data
    user = update.effective_user

    if query.data == "main_menu":
        keyboard = get_main_menu_keyboard(user.id)
        await query.edit_message_text("📋 Menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))
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

    if query.data == "menu_cang3d":
        user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy 2 số để ghép càng 3D:")
        return

    if query.data == "menu_cang4d":
        user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text("📥 Nhập dãy 3 số để ghép càng 4D:")
        return

    if query.data == "reset_state":
        user_data.clear()
        keyboard = get_main_menu_keyboard(user.id)
        await query.edit_message_text("✅ Đã reset trạng thái. Quay về Menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))
        return


# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ Hướng dẫn sử dụng bot:

🧮 Ghép xiên:
- Vào menu "Ghép xiên"
- Chọn độ dài (2, 3 hoặc 4 số)
- Nhập dãy số (VD: 12 34 56 78...)

🔢 Ghép càng:
- Vào "Ghép càng 3D" hoặc "4D"
- Nhập các số (VD: 12 34 56)
- Sau đó nhập các càng muốn ghép (VD: 1 2 3)

🔄 Reset trạng thái nếu muốn làm lại thao tác.

📩 Mọi lỗi vui lòng báo admin."""
    await update.message.reply_text(text)

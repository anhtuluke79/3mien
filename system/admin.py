from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

# Đặt ID admin tại đây hoặc import từ biến môi trường nếu muốn bảo mật hơn
ADMIN_IDS = {123456789, 987654321}  # Sửa thành các user_id thực tế của bạn

def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Xem log sử dụng", callback_data="admin_view_log")],
        # Thêm nút quản trị khác tại đây
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Simple log (dùng file hoặc database tuỳ bạn)
def log_user_action(action):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            with open("user_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{user.id}|{user.username}|{user.first_name}|{action}\n")
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "🛡️ *Menu quản trị* (dành cho admin):\n- Xem log sử dụng\n- Quản lý menu khác (nâng cấp sau)"
    if user_id not in ADMIN_IDS:
        text = "⛔ Bạn không có quyền truy cập menu quản trị!"
        if getattr(update, "message", None):
            await update.message.reply_text(text, parse_mode="Markdown")
        elif getattr(update, "callback_query", None):
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        return

    if getattr(update, "message", None):
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())
    elif getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Bạn không có quyền truy cập!", parse_mode="Markdown")
        return
    if data == "admin_view_log":
        try:
            with open("user_log.txt", "r", encoding="utf-8") as f:
                log_lines = f.readlines()[-30:]  # Hiển thị 30 dòng cuối cùng
            log_text = "*Log sử dụng gần nhất:*\n" + "".join([f"- {line}" for line in log_lines])
        except Exception:
            log_text = "Không có log nào."
        await query.edit_message_text(log_text[:4096], parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())
    else:
        await query.edit_message_text("❓ Chức năng quản trị chưa hỗ trợ.", reply_markup=get_admin_menu_keyboard())

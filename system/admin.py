import os
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# === Lấy ADMIN_IDS từ biến môi trường ===
def get_admin_ids():
    raw = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]

ADMIN_IDS = get_admin_ids()

# === Hàm ghi log hoạt động bot ===
def write_user_log(update, action):
    user = update.effective_user
    chat = update.effective_chat
    with open("bot_usage.log", "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chat.id,
            getattr(chat, "title", ""),
            getattr(user, "id", ""),
            getattr(user, "username", ""),
            getattr(user, "full_name", ""),
            action
        ])

# === Decorator log tự động cho handler ===
def log_user_action(action_desc):
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            write_user_log(update, action_desc)
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# === Menu quản trị chỉ cho admin ===
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📜 Xem log sử dụng", callback_data="admin_log")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === Callback handler cho menu admin ===
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Bạn không có quyền truy cập menu quản trị!", reply_markup=None)
        return

    data = query.data
    if data == "admin_log":
        # Đọc file log, chỉ trả về 50 dòng gần nhất để tránh dài
        log_text = ""
        try:
            with open("bot_usage.log", encoding="utf-8") as f:
                lines = f.readlines()[-50:]
                log_text = "*50 hoạt động gần nhất:*\n" + "".join(lines)
            if len(log_text) > 3800:
                log_text = log_text[-3800:]
        except Exception as e:
            log_text = f"Không đọc được log: {e}"
        await query.edit_message_text(
            f"<pre>{log_text}</pre>",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await query.edit_message_text("⛔ Lệnh quản trị không hợp lệ!", reply_markup=get_admin_menu_keyboard())

# === Command mở menu admin (chỉ admin mới dùng) ===
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập menu quản trị!")
        return
    await update.message.reply_text(
        "🛡️ *MENU QUẢN TRỊ BOT*\nChỉ admin mới thấy được menu này.",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="Markdown"
    )

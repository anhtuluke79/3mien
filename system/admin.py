import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
import threading

# ========== ADMIN IDS ==========
ADMIN_IDS = set(
    int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")
)

# ========== KEYBOARDS ==========
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Xem log sử dụng", callback_data="admin_view_log")],
        [InlineKeyboardButton("📥 Crawl XSMB (chọn số ngày)", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên GitHub", callback_data="admin_upload_github")],
        [InlineKeyboardButton("📤 Tải file xsmb.csv", callback_data="admin_download_csv")],
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_crawl_days_keyboard():
    keyboard = [
        [InlineKeyboardButton("10 ngày", callback_data="admin_crawl_days_10"),
         InlineKeyboardButton("30 ngày", callback_data="admin_crawl_days_30")],
        [InlineKeyboardButton("60 ngày", callback_data="admin_crawl_days_60"),
         InlineKeyboardButton("100 ngày", callback_data="admin_crawl_days_100")],
        [InlineKeyboardButton("⬅️ Quản trị", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== LOG DECORATOR ==========
def log_user_action(action):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            with open("user_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{user.id}|{user.username}|{user.first_name}|{action}\n")
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# ========== ADMIN MENU ==========
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "🛡️ *Menu quản trị* (chỉ admin):\n- Xem log\n- Crawl XSMB\n- Upload lên GitHub\n- Tải file csv\n- ..."
    if user_id not in ADMIN_IDS:
        text = "⛔ Bạn không có quyền truy cập menu quản trị!"
        if getattr(update, "message", None):
            await update.message.reply_text(text, parse_mode="Markdown")
        elif getattr(update, "callback_query", None):
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        return

    if getattr(update, "message", None):
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())
    elif getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())

# ========== CALLBACK HANDLER ==========
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Bạn không có quyền truy cập!", parse_mode="Markdown")
        return

    # ---- XEM LOG ----
    if data == "admin_view_log":
        try:
            with open("user_log.txt", "r", encoding="utf-8") as f:
                log_lines = f.readlines()[-30:]
            log_text = "*Log sử dụng gần nhất:*\n" + "".join([f"- {line}" for line in log_lines])
        except Exception:
            log_text = "Không có log nào."
        await query.edit_message_text(log_text[:4096], parse_mode="Markdown", reply_markup=get_admin_menu_keyboard())
        return

    # ---- CRAWL XSMB (chọn số ngày) ----
    elif data == "admin_crawl_xsmb":
        await query.edit_message_text(
            "Chọn số ngày muốn crawl dữ liệu XSMB:",
            reply_markup=get_crawl_days_keyboard()
        )
        return

    elif data.startswith("admin_crawl_days_"):
        days = int(data.split("_")[-1])
        await query.edit_message_text(
            f"⏳ Đang crawl {days} ngày XSMB, vui lòng đợi...",
            reply_markup=get_admin_menu_keyboard()
        )
        async def async_crawl_and_send(chat_id, context, days):
            try:
                from utils.crawler import crawl_xsmb_Nngay_minhchinh_csv
                df = crawl_xsmb_Nngay_minhchinh_csv(days, "xsmb.csv", delay_sec=6, use_random_delay=True)
                if df is not None and not df.empty:
                    msg = f"✅ Đã crawl xong {days} ngày XSMB!\nSố dòng hiện có: {len(df)}.\nGửi file xsmb.csv về cho bạn."
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=open("xsmb.csv", "rb"),
                        filename="xsmb.csv",
                        caption=msg
                    )
                else:
                    await context.bot.send_message(chat_id, f"❌ Lỗi: Crawl không thành công hoặc không có dữ liệu mới!")
            except Exception as e:
                await context.bot.send_message(chat_id, f"❌ Lỗi khi crawl: {e}")

        # Tạo task chạy async trong event loop
        loop = context.application.create_task(
            async_crawl_and_send(query.message.chat_id, context, days)
        )
        return

    # ---- UPLOAD xsmb.csv lên GITHUB ----
    elif data == "admin_upload_github":
        await query.edit_message_text(
            "⏳ Đang upload file xsmb.csv lên GitHub, vui lòng đợi...",
            reply_markup=get_admin_menu_keyboard()
        )
        def do_upload(chat_id, context):
            try:
                from utils.upload_github import upload_file_to_github
                github_token = os.getenv("GITHUB_TOKEN")
                upload_file_to_github(
                    local_file_path="xsmb.csv",
                    repo_name="anhtuluke79/3mien",
                    remote_path="xsmb.csv",
                    commit_message="Cập nhật xsmb.csv từ Telegram admin",
                    github_token=github_token
                )
                context.bot.send_message(chat_id, "✅ Đã upload xsmb.csv lên GitHub thành công!", reply_markup=get_admin_menu_keyboard())
            except Exception as e:
                context.bot.send_message(chat_id, f"❌ Lỗi khi upload GitHub: {e}", reply_markup=get_admin_menu_keyboard())
        threading.Thread(target=do_upload, args=(query.message.chat_id, context)).start()
        return

    # ---- TẢI FILE XSMB.CSV ----
    elif data == "admin_download_csv":
        try:
            await query.edit_message_text("Đang gửi file xsmb.csv cho bạn...", reply_markup=get_admin_menu_keyboard())
            with open("xsmb.csv", "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename="xsmb.csv",
                    caption="📤 Đây là file xsmb.csv mới nhất!"
                )
        except Exception as e:
            await query.edit_message_text(f"❌ Lỗi gửi file: {e}", reply_markup=get_admin_menu_keyboard())
        return

    # ---- DEFAULT ----
    else:
        await query.edit_message_text("❓ Chức năng quản trị chưa hỗ trợ.", reply_markup=get_admin_menu_keyboard())


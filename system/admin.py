import os
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import utils.thongkemb as tk
import utils.ai_rf as ai_rf

# ========== ADMIN IDS ==========
ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(","))

# ========== KEYBOARDS ==========
def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Xem log sử dụng", callback_data="admin_view_log")],
        [InlineKeyboardButton("📥 Crawl XSMB (chọn số ngày)", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên GitHub", callback_data="admin_upload_github")],
        [InlineKeyboardButton("📤 Tải file xsmb.csv", callback_data="admin_download_csv")],
        [InlineKeyboardButton("🤖 Train AI Random Forest", callback_data="admin_train_rf")],
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

def get_ai_rf_ngay_keyboard():
    keyboard = [
        [InlineKeyboardButton("7 ngày", callback_data="admin_train_rf_N_7"),
         InlineKeyboardButton("14 ngày", callback_data="admin_train_rf_N_14")],
        [InlineKeyboardButton("21 ngày", callback_data="admin_train_rf_N_21"),
         InlineKeyboardButton("28 ngày", callback_data="admin_train_rf_N_28")],
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
    text = (
        "🛡️ *Menu quản trị* (chỉ admin):\n"
        "- Xem log\n"
        "- Crawl XSMB\n"
        "- Upload lên GitHub\n"
        "- Train AI Random Forest\n"
        "- ... (nâng cấp sau)"
    )
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

# ========== ASYNC SUPPORT ==========
async def do_upload_and_send(context, chat_id):
    from utils.upload_github import upload_file_to_github
    github_token = os.getenv("GITHUB_TOKEN")
    try:
        await asyncio.to_thread(
            upload_file_to_github,
            "xsmb.csv",
            "anhtuluke79/3mien",
            "xsmb.csv",
            "Cập nhật xsmb.csv từ bot Telegram",
            github_token
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Đã upload xsmb.csv lên GitHub thành công!",
            reply_markup=get_admin_menu_keyboard()
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Lỗi khi upload GitHub: {e}",
            reply_markup=get_admin_menu_keyboard()
        )

async def do_crawl_and_send(context, chat_id, days):
    from utils.crawler import crawl_xsmb_Nngay_minhchinh_csv
    try:
        df = await asyncio.to_thread(
            crawl_xsmb_Nngay_minhchinh_csv,
            days, "xsmb.csv", 6, True
        )
        if df is not None and not df.empty:
            msg = f"✅ Đã crawl xong {days} ngày XSMB!\nSố dòng hiện có: {len(df)}.\nGửi file xsmb.csv về cho bạn."
            with open("xsmb.csv", "rb") as f:
                await context.bot.send_document(chat_id, f, filename="xsmb.csv", caption=msg)
        else:
            await context.bot.send_message(chat_id, "❌ Lỗi: Crawl không thành công hoặc không có dữ liệu mới!")
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Lỗi khi crawl: {e}")

async def do_train_rf_and_send(context, chat_id, N):
    try:
        msg = await asyncio.to_thread(ai_rf.train_rf_model, num_days=N, data_path="xsmb.csv")
        await context.bot.send_message(chat_id, msg, reply_markup=get_admin_menu_keyboard())
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Lỗi khi train AI: {e}", reply_markup=get_admin_menu_keyboard())

# ========== CALLBACK HANDLER ==========
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Bạn không có quyền truy cập!", parse_mode="Markdown")
        return

    if data == "admin_menu":
        await admin_menu(update, context)
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
        chat_id = update.effective_chat.id
        asyncio.create_task(do_crawl_and_send(context, chat_id, days))
        return

    # ---- UPLOAD xsmb.csv lên GITHUB ----
    elif data == "admin_upload_github":
        await query.edit_message_text(
            "⏳ Đang upload file xsmb.csv lên GitHub, vui lòng đợi...",
            reply_markup=get_admin_menu_keyboard()
        )
        chat_id = update.effective_chat.id
        asyncio.create_task(do_upload_and_send(context, chat_id))
        return

    # ---- TẢI FILE CSV ----
    elif data == "admin_download_csv":
        if not os.path.exists("xsmb.csv"):
            await query.edit_message_text("❌ Không tìm thấy file xsmb.csv!", reply_markup=get_admin_menu_keyboard())
        else:
            await query.edit_message_text("Đang gửi file xsmb.csv về cho bạn...", reply_markup=get_admin_menu_keyboard())
            with open("xsmb.csv", "rb") as f:
                await context.bot.send_document(update.effective_chat.id, f, filename="xsmb.csv", caption="File xsmb.csv")

    # ---- TRAIN AI RANDOM FOREST ----
    elif data == "admin_train_rf":
        await query.edit_message_text(
            "Chọn số ngày để train AI Random Forest:",
            reply_markup=get_ai_rf_ngay_keyboard()
        )
        return
    elif data.startswith("admin_train_rf_N_"):
        N = int(data.split("_")[-1])
        await query.edit_message_text(f"⏳ Đang train AI Random Forest với {N} ngày, vui lòng đợi...", reply_markup=get_admin_menu_keyboard())
        chat_id = update.effective_chat.id
        asyncio.create_task(do_train_rf_and_send(context, chat_id, N))
        return

    # ---- DEFAULT ----
    else:
        await query.edit_message_text("❓ Chức năng quản trị chưa hỗ trợ.", reply_markup=get_admin_menu_keyboard())

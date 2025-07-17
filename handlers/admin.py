# handlers/admin.py

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.ai_rf.rf_db import train_rf_db
from utils.ai_rf.rf_lo import train_rf_lo_mb
from utils.crawl.crawl_xsmb import crawl_xsmb_Nngay_minhchinh_csv
from utils.upload_github import upload_file_to_github  # tạo file này
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

# Hàm menu admin
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bạn không có quyền truy cập menu admin!")
        return
    keyboard = [
        [InlineKeyboardButton("⚙️ Train lại AI RF ĐB", callback_data="train_model_db")],
        [InlineKeyboardButton("⚙️ Train lại AI RF Lô", callback_data="train_model_lo")],
        [InlineKeyboardButton("🔄 Cập nhật XSMB", callback_data="capnhat_xsmb")],
        [InlineKeyboardButton("⬆️ Upload CSV lên GitHub", callback_data="upload_csv_github")],
        [InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu")],
    ]
    await update.message.reply_text(
        "<b>🛠️ Menu quản trị bot</b>\nChọn chức năng dành cho admin:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# Callback cho các chức năng admin
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này!")
        return

    if query.data == "train_model_db":
        await query.edit_message_text("⏳ Đang train AI RF ĐB...")
        ok = train_rf_db("xsmb.csv", "model_rf_xsmb.pkl", 7)
        if ok:
            await query.message.reply_text("✅ Train xong AI RF giải ĐB!")
        else:
            await query.message.reply_text("❌ Train thất bại hoặc thiếu file dữ liệu.")

    elif query.data == "train_model_lo":
        await query.edit_message_text("⏳ Đang train AI RF Lô...")
        ok = train_rf_lo_mb("xsmb.csv", "model_rf_lo_mb.pkl", 7)
        if ok:
            await query.message.reply_text("✅ Train xong AI RF Lô!")
        else:
            await query.message.reply_text("❌ Train thất bại hoặc thiếu file dữ liệu.")

    elif query.data == "capnhat_xsmb":
        await query.edit_message_text("⏳ Đang cập nhật XSMB...")
        df = crawl_xsmb_Nngay_minhchinh_csv(60, "xsmb.csv")
        if df is not None:
            await query.message.reply_text(f"✅ Đã cập nhật file xsmb.csv ({len(df)} ngày, không trùng lặp ngày).")
        else:
            await query.message.reply_text("❌ Không có dữ liệu mới nào để cập nhật.")

    elif query.data == "upload_csv_github":
        await query.edit_message_text("⏳ Đang upload xsmb.csv lên GitHub...")
        token = os.getenv("GITHUB_TOKEN")
        ok = upload_file_to_github("xsmb.csv", "anhtuluke79/3mien", "xsmb.csv", token)
        if ok:
            await query.message.reply_text("✅ Upload xsmb.csv lên GitHub thành công!")
        else:
            await query.message.reply_text("❌ Upload thất bại. Kiểm tra token hoặc quyền repo!")

    elif query.data == "main_menu":
        from handlers.menu import menu
        await menu(update, context)

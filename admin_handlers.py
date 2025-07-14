from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from user_manage import is_super_admin
from logic_xsmb import (
    crawl_xsmb_15ngay_minhchinh_csv, train_rf_model_main,
    backup_files, restore_files
)
import os
import subprocess

async def admin_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("🧠 Train & Lưu model", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬆️ Upload model lên Github", callback_data="admin_upload_model")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên Github", callback_data="admin_upload_csv")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

async def backup_restore_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📤 Backup dữ liệu", callback_data="backup_data")],
        [InlineKeyboardButton("📥 Restore dữ liệu", callback_data="restore_data")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("🗂 Backup / Restore dữ liệu:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_callback_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if not is_super_admin(user_id):
        await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này.")
        return

    # CRAWL
    if data == "admin_crawl_xsmb":
        await query.edit_message_text("⏳ Đang crawl XSMB 15 ngày gần nhất, vui lòng đợi...")
        try:
            df = crawl_xsmb_15ngay_minhchinh_csv()
            if df is not None:
                await query.message.reply_document(document=open(os.path.join("xsmb.csv"), "rb"),
                                                  filename="xsmb.csv",
                                                  caption="✅ Đã crawl xong, đây là file xsmb.csv mới nhất!")
                # Tự động commit & push lên Github nếu cần
                try:
                    subprocess.run(["git", "add", "xsmb.csv"], check=True)
                    subprocess.run(["git", "commit", "-m", "update xsmb.csv (auto after crawl)"], check=True)
                    subprocess.run(["git", "push"], check=True)
                    await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
                except Exception as e:
                    await query.message.reply_text(f"❌ Lỗi upload xsmb.csv lên Github: {e}")
            else:
                await query.message.reply_text("❌ Không crawl được dữ liệu nào!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi crawl: {e}")
        return

    # TRAIN
    if data == "admin_train_rf":
        await query.edit_message_text("⏳ Đang train model RF...")
        ok, msg = train_rf_model_main()
        await query.message.reply_text(msg)
        if ok:
            try:
                subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
                subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl (auto after train)"], check=True)
                subprocess.run(["git", "push"], check=True)
                await query.message.reply_text("✅ Đã upload rf_model_xsmb.pkl lên Github!")
            except Exception as e:
                await query.message.reply_text(f"❌ Lỗi upload model lên Github: {e}")
        return

    # UPLOAD model thủ công
    if data == "admin_upload_model":
        await query.edit_message_text("⏳ Đang upload model rf_model_xsmb.pkl lên Github...")
        try:
            subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload file model rf_model_xsmb.pkl lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload model: {e}")
        return

    # UPLOAD xsmb.csv thủ công
    if data == "admin_upload_csv":
        await query.edit_message_text("⏳ Đang upload xsmb.csv lên Github...")
        try:
            subprocess.run(["git", "add", "xsmb.csv"], check=True)
            subprocess.run(["git", "commit", "-m", "update xsmb.csv"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload: {e}")
        return

    # BACKUP
    if data == "backup_data":
        backed = backup_files()
        msg = "📤 Đã backup: " + ", ".join(backed)
        for file_path in backed:
            with open(file_path, "rb") as f:
                await query.message.reply_document(document=InputFile(f))
        await query.edit_message_text(msg)
        return

    # RESTORE
    if data == "restore_data":
        restored = restore_files()
        msg = "📥 Đã restore: " + ", ".join(restored)
        await query.edit_message_text(msg)
        return

    if data == "main_menu":
        from menu_handlers import menu
        await menu(update, context)
        return

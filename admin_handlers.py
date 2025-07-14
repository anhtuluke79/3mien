import os
import subprocess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import ContextTypes

from logic_xsmb import crawl_xsmb_15ngay_minhchinh_csv, train_rf_model_main
from user_manage import list_users, approve_user, remove_user

GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH", ".")

SUPER_ADMIN_IDS = [int(x) for x in os.getenv("SUPER_ADMIN_IDS", "").split(",") if x.strip().isdigit()]

def is_super_admin(user_id):
    return int(user_id) in SUPER_ADMIN_IDS

# ============ MENU ADMIN ============
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("🧠 Train & Lưu model", callback_data="admin_train_rf")],
        [InlineKeyboardButton("⬆️ Upload model lên Github", callback_data="admin_upload_model")],
        [InlineKeyboardButton("⬆️ Upload xsmb.csv lên Github", callback_data="admin_upload_csv")],
        [InlineKeyboardButton("👥 Quản lý user", callback_data="user_manage_menu")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("⚙️ Menu quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

# ============ CALLBACK HANDLER ============
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # --- Chỉ cho super admin ---
    if not is_super_admin(user_id):
        await query.edit_message_text("❌ Bạn không có quyền truy cập chức năng quản trị!")
        return

    # -- MENU ADMIN --
    if data == "admin_menu":
        await admin_menu(update, context)
        return

    # --- CRAWL XSMB ---
    if data == "admin_crawl_xsmb":
        await query.edit_message_text("⏳ Đang crawl XSMB 15 ngày gần nhất...")
        df = crawl_xsmb_15ngay_minhchinh_csv()
        if df is not None:
            csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
            await query.message.reply_document(document=open(csv_path, "rb"), filename="xsmb.csv", caption="✅ Đã crawl xong, đây là file xsmb.csv mới nhất!")
            # Push lên Github
            try:
                os.chdir(GITHUB_REPO_PATH)
                subprocess.run(["git", "add", "xsmb.csv"], check=True)
                subprocess.run(["git", "commit", "-m", "update xsmb.csv (auto after crawl)"], check=True)
                subprocess.run(["git", "push"], check=True)
                await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
            except Exception as e:
                await query.message.reply_text(f"❌ Lỗi upload xsmb.csv lên Github: {e}")
        else:
            await query.message.reply_text("❌ Không crawl được dữ liệu nào!")
        return

    # --- TRAIN MODEL ---
    if data == "admin_train_rf":
        await query.edit_message_text("⏳ Đang train model RF...")
        ok, msg = train_rf_model_main()
        await query.message.reply_text(msg)
        if ok:
            try:
                os.chdir(GITHUB_REPO_PATH)
                subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
                subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl (auto after train)"], check=True)
                subprocess.run(["git", "push"], check=True)
                await query.message.reply_text("✅ Đã upload rf_model_xsmb.pkl lên Github!")
            except Exception as e:
                await query.message.reply_text(f"❌ Lỗi upload model lên Github: {e}")
        return

    # --- UPLOAD MODEL ---
    if data == "admin_upload_model":
        await query.edit_message_text("⏳ Đang upload model rf_model_xsmb.pkl lên Github...")
        try:
            os.chdir(GITHUB_REPO_PATH)
            subprocess.run(["git", "add", "rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "commit", "-m", "update model rf_model_xsmb.pkl"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload file model rf_model_xsmb.pkl lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload model: {e}")
        return

    # --- UPLOAD CSV ---
    if data == "admin_upload_csv":
        await query.edit_message_text("⏳ Đang upload xsmb.csv lên Github...")
        try:
            os.chdir(GITHUB_REPO_PATH)
            subprocess.run(["git", "add", "xsmb.csv"], check=True)
            subprocess.run(["git", "commit", "-m", "update xsmb.csv"], check=True)
            subprocess.run(["git", "push"], check=True)
            await query.message.reply_text("✅ Đã upload xsmb.csv lên Github!")
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi upload: {e}")
        return

    # --- QUẢN LÝ USER ---
    if data == "user_manage_menu":
        users = list_users()
        keyboard = []
        for u in users:
            status = "Đã duyệt" if u["approved"] else "Chờ duyệt"
            btn_text = f'{u["username"]} ({status})'
            if u["approved"]:
                keyboard.append([InlineKeyboardButton(f'❌ Xóa {u["username"]}', callback_data=f"user_manage_remove_{u['user_id']}")])
            else:
                keyboard.append([InlineKeyboardButton(f'✅ Duyệt {u["username"]}', callback_data=f"user_manage_approve_{u['user_id']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Quay lại admin", callback_data="admin_menu")])
        await query.edit_message_text("👥 Quản lý user:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # --- DUYỆT USER ---
    if data.startswith("user_manage_approve_"):
        user_id_approve = int(data.split("_")[-1])
        approve_user(user_id_approve)
        await query.edit_message_text(f"✅ Đã duyệt user: {user_id_approve}")
        return

    # --- XÓA USER ---
    if data.startswith("user_manage_remove_"):
        user_id_remove = int(data.split("_")[-1])
        remove_user(user_id_remove)
        await query.edit_message_text(f"❌ Đã xóa user: {user_id_remove}")
        return

    # --- QUAY LẠI MENU ---
    if data == "main_menu":
        from menu_handlers import menu
        await menu(update, context)
        return

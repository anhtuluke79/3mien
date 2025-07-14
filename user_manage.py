import json
import os
from config import SUPER_ADMIN_IDS, ALLOWED_GROUP_IDS

ALLOWED_USERS_FILE = "allowed_users.json"

def load_allowed_users():
    try:
        with open(ALLOWED_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {str(uid): {"name": "SuperAdmin", "date": "init"} for uid in SUPER_ADMIN_IDS}

def save_allowed_users(users_dict):
    with open(ALLOWED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def is_super_admin(user_id):
    return int(user_id) in SUPER_ADMIN_IDS

def is_allowed_user(user_id):
    users = load_allowed_users()
    return str(user_id) in users or is_super_admin(user_id)

def is_allowed_group(chat):
    # Đảm bảo chỉ cho phép chạy bot ở các nhóm cho phép
    return chat.type in ("group", "supergroup") and int(chat.id) in ALLOWED_GROUP_IDS

async def listusers(update, context):
    if not is_super_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    users = load_allowed_users()
    if not users:
        await update.message.reply_text("Chưa có user nào được duyệt.")
        return
    msg = "📋 *Danh sách user đã duyệt:*\n"
    for uid, info in users.items():
        msg += f"- `{uid}`: {info.get('name','')} (duyệt: {info.get('date','')})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def deluser(update, context):
    if not is_super_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    if not context.args:
        await update.message.reply_text("Dùng: /deluser <user_id>")
        return
    user_id = context.args[0]
    users = load_allowed_users()
    if user_id in users:
        info = users[user_id]
        del users[user_id]
        save_allowed_users(users)
        await update.message.reply_text(f"❌ Đã xóa quyền user {user_id} ({info.get('name','')})")
    else:
        await update.message.reply_text("User này không có trong danh sách duyệt.")

async def block_unapproved(update, context):
    user = update.effective_user
    chat = update.effective_chat
    if not is_allowed_group(chat):
        return
    if not is_allowed_user(user.id):
        await update.message.reply_text("⏳ Bạn chưa được duyệt sử dụng bot, vui lòng chờ admin xét duyệt.")
        return

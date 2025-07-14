import os
import json

USERS_FILE = "users.json"

SUPER_ADMIN_IDS = [int(x) for x in os.getenv("SUPER_ADMIN_IDS", "").split(",") if x.strip().isdigit()]
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# -- Đọc danh sách user từ file json --
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

# -- Ghi danh sách user vào file json --
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# -- Thêm user mới (chưa duyệt) --
def add_user(user_id, username):
    users = load_users()
    if any(u["user_id"] == user_id for u in users):
        return
    users.append({"user_id": user_id, "username": username, "approved": False})
    save_users(users)

# -- Duyệt user --
def approve_user(user_id):
    users = load_users()
    for u in users:
        if u["user_id"] == user_id:
            u["approved"] = True
    save_users(users)

# -- Xóa user --
def remove_user(user_id):
    users = load_users()
    users = [u for u in users if u["user_id"] != user_id]
    save_users(users)

# -- Trả về danh sách user (dạng list of dict) --
def list_users():
    return load_users()

# -- Kiểm tra quyền super admin --
def is_super_admin(user_id):
    return int(user_id) in SUPER_ADMIN_IDS

# -- Kiểm tra quyền admin --
def is_admin(user_id):
    return int(user_id) in ADMIN_IDS or is_super_admin(user_id)

# -- Kiểm tra user đã duyệt chưa --
def is_approved(user_id):
    users = load_users()
    for u in users:
        if u["user_id"] == user_id:
            return u["approved"]
    return False

# -- Callback menu quản lý user (trả menu về admin_handlers nếu cần) --
async def user_manage_callback_handler(update, context):
    query = update.callback_query
    data = query.data

    # Danh sách user (menu callback: user_manage_menu)
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

    # Duyệt user (user_manage_approve_USERID)
    if data.startswith("user_manage_approve_"):
        user_id_approve = int(data.split("_")[-1])
        approve_user(user_id_approve)
        await query.edit_message_text(f"✅ Đã duyệt user: {user_id_approve}")
        return

    # Xóa user (user_manage_remove_USERID)
    if data.startswith("user_manage_remove_"):
        user_id_remove = int(data.split("_")[-1])
        remove_user(user_id_remove)
        await query.edit_message_text(f"❌ Đã xóa user: {user_id_remove}")
        return

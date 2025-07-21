import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

raw_admin_ids = os.getenv("ADMIN_IDS")
if not raw_admin_ids:
    raise ValueError("ADMIN_IDS chưa được thiết lập!")
ADMIN_IDS = list(map(int, raw_admin_ids.split(',')))

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

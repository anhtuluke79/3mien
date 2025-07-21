from itertools import combinations, permutations

# Kiểm tra quyền admin
def is_admin(user_id, admin_ids):
    return int(user_id) in admin_ids

# Tách số
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

# Ghép xiên
def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    return ['&'.join(comb) for comb in combinations(numbers, do_dai)]

# Đảo số
def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

# Giao diện chính
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard(user_id, admin_ids):
    keyboard = [
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
    ]
    if is_admin(user_id, admin_ids):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

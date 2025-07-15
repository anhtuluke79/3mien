# utils/utils.py

import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

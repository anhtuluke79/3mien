import os
import asyncio
import aiosqlite
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import base64

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from itertools import combinations, permutations

# ======= IMPORT MODULE PHONG THỦY =======
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ========== CONFIG & GITHUB ==========
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or "YOUR_PERSONAL_ACCESS_TOKEN"
GITHUB_OWNER = "anhtuluke79"
GITHUB_REPO = "3mien"
GITHUB_BRANCH = "main"
CSV_FILES = {
    "xsmb.csv": "xsmb.csv",
    "xsmt.csv": "xsmt.csv",
    "xsmn.csv": "xsmn.csv"
}
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TOKEN_HERE"
DB_PATH = "bot_data.db"
XSMB_CSV = "xsmb.csv"
XSMT_CSV = "xsmt.csv"
XSMN_CSV = "xsmn.csv"

# ========== DB INIT & ADMIN ==========
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                content TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_config (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                config_json TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_at TEXT DEFAULT (datetime('now')),
                is_superadmin INTEGER DEFAULT 0
            )
        """)
        superadmin_id = int(os.getenv("SUPERADMIN_ID", "12345678"))
        superadmin_username = os.getenv("SUPERADMIN_USERNAME", "superadmin")
        await db.execute(
            "INSERT OR IGNORE INTO admin (user_id, username, is_superadmin) VALUES (?, ?, 1)",
            (superadmin_id, superadmin_username)
        )
        await db.commit()

async def is_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admin WHERE user_id = ?", (int(user_id),)) as cursor:
            row = await cursor.fetchone()
            return bool(row)

async def add_admin(user_id, username, is_superadmin=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admin (user_id, username, is_superadmin) VALUES (?, ?, ?)",
            (int(user_id), username, int(is_superadmin))
        )
        await db.commit()

async def add_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_superadmin FROM admin WHERE user_id = ?", (user.id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] != 1:
                await update.message.reply_text("❌ Bạn không có quyền thêm admin.")
                return
    try:
        new_id = int(context.args[0])
        new_username = context.args[1] if len(context.args) > 1 else ""
        await add_admin(new_id, new_username)
        await update.message.reply_text(f"✅ Đã thêm admin {new_username} ({new_id}) thành công!")
    except Exception:
        await update.message.reply_text("Cách dùng: /addadmin <user_id> [username]")

async def log_user_action(user, action, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_log (user_id, username, action, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username or user.full_name or "", action, content, datetime.now().isoformat())
        )
        await db.commit()

# ========== UTILITIES ==========
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

def get_can_chi_ngay(year, month, day):
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    can = can_list[(jd + 9) % 10]
    chi = chi_list[(jd + 1) % 12]
    return f"{can} {chi}"

def sinh_so_hap_cho_ngay(can_chi_str):
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code: return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j: ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can,
        "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"),
        "so_menh": so_menh,
        "so_hap_list": so_ghep,
        "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else:
        so_hap_can = "?"
        so_menh = "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 Số Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Số phong thủy ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n"
        f"- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n"
        f"- Số hạp ngày: {so_hap_ngay}"
    )
    return text

def chot_so_format(can_chi, sohap_info, today_str):
    if not sohap_info or not sohap_info.get("so_hap_list"):
        return "Không đủ dữ liệu phong thủy để chốt số hôm nay!"
    d = [sohap_info['so_menh']] + sohap_info['so_hap_list']
    chams = ','.join(d)
    dan_de = []
    for x in d:
        for y in d:
            dan_de.append(x + y)
    dan_de = sorted(set(dan_de))
    lo = []
    for x in d:
        for y in d:
            if x != y:
                lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n"
        f"*Chốt số 3 miền ngày {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\n"
        f"Lô: {', '.join(lo)}"
    )
    return text

# ========== MENU UI ==========
async def build_main_menu(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🧧 Thần tài gợi ý", callback_data="than_tai_goi_y")],
        [InlineKeyboardButton("🔮 Số Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien"),
         InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def build_than_tai_menu():
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Miền Bắc", callback_data="than_tai_mb_btn"),
         InlineKeyboardButton("🌞 Miền Trung", callback_data="than_tai_mt_btn"),
         InlineKeyboardButton("🌴 Miền Nam", callback_data="than_tai_mn_btn")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_xien_menu():
    keyboard = [
        [InlineKeyboardButton("Xiên 2", callback_data="ghepxien_2"),
         InlineKeyboardButton("Xiên 3", callback_data="ghepxien_3"),
         InlineKeyboardButton("Xiên 4", callback_data="ghepxien_4")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_admin_menu():
    keyboard = [
        [InlineKeyboardButton("📥 Cập nhật XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("📥 Cập nhật XSMT", callback_data="admin_crawl_xsmt")],
        [InlineKeyboardButton("📥 Cập nhật XSMN", callback_data="admin_crawl_xsmn")],
        [InlineKeyboardButton("📤 Đẩy dữ liệu CSV lên GitHub", callback_data="admin_pushcsv")],
        [InlineKeyboardButton("➕ Thêm admin", callback_data="admin_add_admin")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ASYNC CRAWL (DEMO: GIẢ LẬP 15 NGÀY) ==========
async def async_crawl_xsmb_15ngay():
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        records.append({"date": date.strftime("%Y-%m-%d"), "DB": f"{i+12345}", "G1": f"{i+20000}"})
    df = pd.DataFrame(records)
    df.to_csv(XSMB_CSV, index=False, encoding="utf-8-sig")
    return df

async def async_crawl_xsmt_15ngay():
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        records.append({"date": date.strftime("%Y-%m-%d"), "DB": f"{i+55555}", "G1": f"{i+11111}"})
    df = pd.DataFrame(records)
    df.to_csv(XSMT_CSV, index=False, encoding="utf-8-sig")
    return df

async def async_crawl_xsmn_15ngay():
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        records.append({"date": date.strftime("%Y-%m-%d"), "DB": f"{i+88888}", "G1": f"{i+22222}"})
    df = pd.DataFrame(records)
    df.to_csv(XSMN_CSV, index=False, encoding="utf-8-sig")
    return df

# ========== AI/ML THỐNG KÊ SỐ ĐẸP ==========
def ai_predict_top2(csv_path):
    df = pd.read_csv(csv_path)
    if "date" in df.columns:
        df = df.sort_values("date", ascending=False).head(15)
    all_numbers = []
    cols = ['DB', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7']
    if "province" in df.columns:
        for _, row in df.iterrows():
            for col in cols:
                if col in df.columns and not pd.isnull(row[col]):
                    numbers = str(row[col]).split()
                    all_numbers += [n[-2:] for n in numbers if n.isdigit() and len(n) >= 2]
    else:
        for col in cols:
            if col in df.columns:
                all_numbers += sum([row.split() for row in df[col].astype(str).tolist()], [])
    two_digit_numbers = [num[-2:] for num in all_numbers if num.isdigit() and len(num) >= 2]
    ser = pd.Series(two_digit_numbers).value_counts()
    top = ser.head(2)
    return top.index.tolist(), top.values.tolist()

# ========== UPLOAD CSV TO GITHUB (3 FILES) ==========
async def upload_csv_to_github(local_file, github_path):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{github_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params={"ref": GITHUB_BRANCH}) as resp:
            if resp.status == 200:
                data = await resp.json()
                sha = data['sha']
            else:
                sha = None
        try:
            with open(local_file, "rb") as f:
                content_bytes = f.read()
        except Exception as e:
            return False, f"Không tìm thấy file {local_file}: {e}"
        content_b64 = base64.b64encode(content_bytes).decode()
        payload = {
            "message": f"Update {github_path} from Telegram Bot",
            "content": content_b64,
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha
        async with session.put(url, headers=headers, json=payload) as resp:
            result = await resp.json()
            if resp.status in (200,201):
                return True, f"✅ Đã cập nhật {github_path} lên GitHub."
            else:
                msg = result.get('message', result)
                return False, f"❌ Lỗi cập nhật {github_path}: {msg}"

async def upload_all_csv_to_github():
    results = []
    for local, github in CSV_FILES.items():
        ok, msg = await upload_csv_to_github(local, github)
        results.append(msg)
    return "\n".join(results)

# ========== MENU & HANDLER ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin_user = await is_admin(user.id)
    await log_user_action(user, action="menu", content="menu")
    markup = await build_main_menu(is_admin_user)
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=markup)
    else:
        await update.callback_query.edit_message_text("🔹 Chọn chức năng:", reply_markup=markup)

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await log_user_action(user, action="menu_callback", content=query.data)
    await query.answer()
    if query.data == "main_menu":
        await menu(update, context)
        return

    # ==== ADMIN MENU ====
    if query.data == "admin_menu":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu quản trị.")
            return
        await query.edit_message_text("⚙️ Menu quản trị:", reply_markup=build_admin_menu())
        return

    if query.data == "admin_crawl_xsmb":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        await query.edit_message_text("Đang cập nhật XSMB...")
        await async_crawl_xsmb_15ngay()
        await query.message.reply_text("✅ Đã cập nhật dữ liệu XSMB.")
        await menu(update, context)
        return

    if query.data == "admin_crawl_xsmt":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        await query.edit_message_text("Đang cập nhật XSMT...")
        await async_crawl_xsmt_15ngay()
        await query.message.reply_text("✅ Đã cập nhật dữ liệu XSMT.")
        await menu(update, context)
        return

    if query.data == "admin_crawl_xsmn":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        await query.edit_message_text("Đang cập nhật XSMN...")
        await async_crawl_xsmn_15ngay()
        await query.message.reply_text("✅ Đã cập nhật dữ liệu XSMN.")
        await menu(update, context)
        return

    if query.data == "admin_pushcsv":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        await query.edit_message_text("Đang đẩy dữ liệu CSV lên GitHub...")
        msg = await upload_all_csv_to_github()
        await query.message.reply_text(msg)
        await menu(update, context)
        return

    if query.data == "admin_add_admin":
        if not await is_admin(user.id):
            await query.edit_message_text("❌ Bạn không có quyền thực hiện thao tác này.")
            return
        context.user_data['wait_input'] = "add_admin"
        await query.edit_message_text("Nhập user_id và username muốn thêm admin, cách nhau dấu cách:\nVí dụ: 12345678 newadmin")
        return

    # ... các callback khác giữ nguyên như cũ ...
    await menu(update, context)

# ========== HANDLER ALL TEXT ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wait_input = context.user_data.get('wait_input')
    if not wait_input:
        return  # Không rep nếu không ở trạng thái nhập liệu!

    user = update.effective_user
    text = update.message.text.strip()

    if wait_input == "add_admin":
        try:
            parts = text.split()
            new_id = int(parts[0])
            new_username = parts[1] if len(parts) > 1 else ""
            await add_admin(new_id, new_username)
            reply = f"✅ Đã thêm admin {new_username} ({new_id}) thành công!"
        except Exception:
            reply = "Sai cú pháp. Nhập: <user_id> <username>"
        context.user_data['wait_input'] = None
        await update.message.reply_text(reply)
        await menu(update, context)
        return

    # Thêm các trạng thái nhập liệu khác nếu muốn (ghép xiên, đảo số, v.v.)

    context.user_data['wait_input'] = None
    return

# ========== HANDLER THẦN TÀI (AI/ML) ==========
async def than_tai_handler(update, context, region):
    user = update.effective_user
    await log_user_action(user, action="ai_than_tai", content=region)
    if region == "MB":
        csv_file = XSMB_CSV
        icon = "🇻🇳"
        tenmien = "miền Bắc"
    elif region == "MT":
        csv_file = XSMT_CSV
        icon = "🌞"
        tenmien = "miền Trung"
    else:
        csv_file = XSMN_CSV
        icon = "🌴"
        tenmien = "miền Nam"
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    try:
        nums, counts = ai_predict_top2(csv_file)
        if len(nums) < 2:
            raise Exception("Chưa đủ dữ liệu thống kê!")
        text = (
            f"{icon} *Thần tài {tenmien} gợi ý*\n"
            f"📅 Dữ liệu 15 ngày gần nhất | Cập nhật: {now}\n"
            f"━━━━━━━━━━━━━\n"
            f"🥇 *Số mạnh 1*: `{nums[0]}` (về {counts[0]} lần)\n"
            f"🥈 *Số mạnh 2*: `{nums[1]}` (về {counts[1]} lần)\n"
            f"━━━━━━━━━━━━━\n"
            f"💡 *Lưu ý:* Chỉ mang tính tham khảo, không đảm bảo trúng thưởng!\n"
            f"_Chúc bạn may mắn & vui vẻ!_ 🎉"
        )
    except Exception as e:
        text = (
            f"{icon} *Thần tài {tenmien} gợi ý*\n"
            f"Không đủ dữ liệu thống kê hoặc lỗi: {e}\n"
            f"Bạn hãy kiểm tra lại file dữ liệu hoặc thử lại sau nhé!\n"
        )
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== BOT STARTUP ==========
async def on_startup(app):
    await init_db()
    print("Bot và DB đã sẵn sàng!")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("addadmin", add_admin_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

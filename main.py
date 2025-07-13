import os
import asyncio
import aiosqlite
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from itertools import combinations, permutations

# ======= IMPORT MODULE PHONG THỦY =======
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ====== CONFIG ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TOKEN_HERE"
DB_PATH = "bot_data.db"
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
XSMB_CSV = "xsmb.csv"
XSMT_CSV = "xsmt.csv"
XSMN_CSV = "xsmn.csv"

# ========== DB INIT ==========
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
        await db.commit()

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

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ========== MENU UI ==========
def build_main_menu():
    keyboard = [
        [InlineKeyboardButton("🧧 Thần tài gợi ý", callback_data="than_tai_goi_y")],
        [InlineKeyboardButton("🔮 Số Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien"),
         InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_than_tai_menu():
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Miền Bắc", callback_data="than_tai_mb_btn"),
         InlineKeyboardButton("🌞 Miền Trung", callback_data="than_tai_mt_btn"),
         InlineKeyboardButton("🌴 Miền Nam", callback_data="than_tai_mn_btn")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ASYNC CRAWL (AIOHTTP SONG SONG) ==========
async def async_crawl_xsmb_1ngay(date):
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date.strftime('%d-%m-%Y')}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as resp:
                html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table")
            table = None
            for tb in tables:
                trs = tb.find_all("tr")
                if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
                    table = tb
                    break
            if not table:
                return None
            result = {"date": date.strftime('%Y-%m-%d')}
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 2: continue
                label = tds[0].get_text(strip=True)
                value = tds[1].get_text(" ", strip=True)
                if "Đặc biệt" in label or "ĐB" in label:
                    match = re.search(r'(\d{5})(?!.*\d)', value)
                    if match:
                        result["DB"] = match.group(1)
                    else:
                        result["DB"] = value
                elif "Nhất" in label: result["G1"] = value
                elif "Nhì" in label: result["G2"] = value
                elif "Ba" in label: result["G3"] = value
                elif "Tư" in label: result["G4"] = value
                elif "Năm" in label: result["G5"] = value
                elif "Sáu" in label: result["G6"] = value
                elif "Bảy" in label: result["G7"] = value
            return result
        except Exception as e:
            print(f"Lỗi crawl {url}: {e}")
            return None

async def crawl_xsmb_15ngay_async():
    today = datetime.today()
    dates = [today - timedelta(days=i) for i in range(15)]
    results = await asyncio.gather(*(async_crawl_xsmb_1ngay(d) for d in dates))
    records = [r for r in results if r]
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("date", ascending=False)
        df.to_csv("xsmb.csv", index=False, encoding="utf-8-sig")
        return df
    return None

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

# ========== MENU & HANDLER ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_action(user, action="menu", content="menu")
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=build_main_menu())
    else:
        await update.callback_query.edit_message_text("🔹 Chọn chức năng:", reply_markup=build_main_menu())

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await log_user_action(user, action="menu_callback", content=query.data)
    await query.answer()

    # Main menu
    if query.data == "main_menu":
        await menu(update, context)
        return

    if query.data == "than_tai_goi_y":
        await query.edit_message_text("🧧 Chọn vùng xổ số bạn muốn Thần tài gợi ý:", reply_markup=build_than_tai_menu())
        return

    if query.data in ["than_tai_mb_btn", "than_tai_mt_btn", "than_tai_mn_btn"]:
        region = {"than_tai_mb_btn": "MB", "than_tai_mt_btn": "MT", "than_tai_mn_btn": "MN"}[query.data]
        await than_tai_handler(update, context, region)
        return

    # Các menu khác: ghép xiên, càng, phong thủy, chốt số, đóng góp... giữ nguyên như cũ, chuyển thành async nếu có.

    # ... (bạn nối tiếp các handler các mục dưới đây)

    await menu(update, context)

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

# ========== HANDLER ALL TEXT ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_action(user, action="text_input", content=update.message.text)
    # ... logic nhập liệu, giống như bản đầy đủ trước đó, nhưng chuyển hết sang async nếu gọi hàm nào lâu hoặc truy xuất db ...

    await update.message.reply_text("Đã nhận dữ liệu. Chức năng này sẽ cập nhật kết quả tương ứng (demo).")
    await menu(update, context)

# ========== BOT STARTUP ==========
async def on_startup(app):
    await init_db()
    print("Bot và DB đã sẵn sàng!")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

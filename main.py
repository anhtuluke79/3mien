import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import shutil
import logging
import re
import joblib
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("🔢 Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    # Nếu cần, kiểm tra admin để thêm nút ADMIN
    user_id = update.effective_user.id if update.effective_user else None
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
        keyboard.append([InlineKeyboardButton("🗂 Backup/Restore", callback_data="backup_restore_menu")])
    # Trả lời đúng kiểu update
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
# ==== DATA ====
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ==== CONFIG ====
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH", ".")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("XSMB-BOT")

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ==== TIỆN ÍCH ====
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
        "can": can, "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"), "so_menh": so_menh,
        "so_hap_list": so_ghep, "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else: so_hap_can, so_menh = "?", "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n- Số hạp ngày: {so_hap_ngay}"
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
            if x != y: lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n*Chốt số hôm nay {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text

# ==== CRAWL XSMB ====
def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    table = None
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            table = tb
            break
    if not table:
        print(f"Không tìm thấy bảng kết quả {date_str}!")
        return None
    result = {"date": f"{nam}-{thang:02d}-{ngay:02d}"}
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

def crawl_xsmb_15ngay_minhchinh_csv(out_csv=None):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            row = crawl_xsmb_1ngay_minhchinh_dict(date.day, date.month, date.year)
            if row:
                records.append(row)
                print(f"✔️ {date.strftime('%d-%m-%Y')} OK")
            time.sleep(1)
        except Exception as e:
            print(f"❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("date", ascending=False)
        if out_csv is None:
            out_csv = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        df.to_csv(oimport os

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("🔢 Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    # Nếu cần, kiểm tra admin để thêm nút ADMIN
    user_id = update.effective_user.id if update.effective_user else None
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
        keyboard.append([InlineKeyboardButton("🗂 Backup/Restore", callback_data="backup_restore_menu")])
    # Trả lời đúng kiểu update
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
# ==== DATA ====
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ==== CONFIG ====
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH", ".")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("XSMB-BOT")

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# ==== TIỆN ÍCH ====
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
        "can": can, "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"), "so_menh": so_menh,
        "so_hap_list": so_ghep, "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else: so_hap_can, so_menh = "?", "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n- Số hạp ngày: {so_hap_ngay}"
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
            if x != y: lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n*Chốt số hôm nay {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text

# ==== CRAWL XSMB ====
def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    table = None
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            table = tb
            break
    if not table:
        print(f"Không tìm thấy bảng kết quả {date_str}!")
        return None
    result = {"date": f"{nam}-{thang:02d}-{ngay:02d}"}
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

def crawl_xsmb_15ngay_minhchinh_csv(out_csv=None):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            row = crawl_xsmb_1ngay_minhchinh_dict(date.day, date.month, date.year)
            if row:
                records.append(row)
                print(f"✔️ {date.strftime('%d-%m-%Y')} OK")
            time.sleep(1)
        except Exception as e:
            print(f"❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("date", ascending=False)
        if out_csv is None:
            out_csv = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu ngày nào!")
        return None

# ==== TRAIN MODEL RF ====
def train_rf_model_main():
    try:
        from train_rf_xsmb import train_rf_model
        csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
        train_rf_model(csv_path=csv_path, model_path=model_path)
        return True, "✅ Đã train xong, lưu rf_model_xsmb.pkl."
    except Exception as e:
        return False, f"❌ Lỗi train model: {e}"

# ==== AI DỰ ĐOÁN ====
def predict_xsmb_rf():
    model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(model_path) or not os.path.exists(csv_path):
        return "❌ Model hoặc dữ liệu xsmb.csv chưa có trên server!"
    model = joblib.load(model_path)
    df = pd.read_csv(csv_path)
    n_feature = getattr(model, "n_features_in_", 6)
    n_day = n_feature // 2
    if len(df) < n_day or 'DB' not in df.columns or 'G1' not in df.columns:
        return f"❌ Dữ liệu không đủ ({len(df)} ngày), cần {n_day} ngày gần nhất!"
    features = []
    for i in range(-n_day, 0):
        day = df.iloc[i]
        features += [int(str(day['DB'])[-2:]), int(str(day['G1'])[-2:])]
    X_pred = [features]
    y_pred = model.predict(X_pred)
    return f"🤖 Thần tài dự đoán giải đặc biệt hôm nay (2 số cuối):\n👉 {str(y_pred[0]).zfill(2)}\n(ML: Random Forest)"

# ==== THỐNG KÊ XỔ SỐ CƠ BẢN ====
def thong_ke_xsmb(n=15):
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(csv_path):
        return "❌ Chưa có file xsmb.csv trên server!"
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return f"❌ Không đọc được xsmb.csv: {e}"
    df = df.sort_values("date", ascending=False)
    msg = "📊 *Thống kê kết quả XSMB %d ngày gần nhất:*\n\n" % n
    msg += "`Ngày       Đặc biệt   Giải nhất`\n"
    msg += "`-----------------------------`\n"
    for _, row in df.head(n).iterrows():
        msg += f"`{row['date']}  {str(row['DB']).rjust(7)}   {str(row['G1']).rjust(7)}`\n"
    return msg

def thong_ke_dau_duoi_db(n=30):
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(csv_path):
        return "❌ Chưa có file xsmb.csv trên server!"
    df = pd.read_csv(csv_path)
    df = df.sort_values("date", ascending=False).head(n)
    db_list = df['DB'].astype(str).str.zfill(5)
    dau = db_list.str[0]
    duoi = db_list.str[-1]
    dau_count = dau.value_counts().sort_index()
    duoi_count = duoi.value_counts().sort_index()
    msg = f"🔢 *Thống kê ĐẦU & ĐUÔI Đặc biệt {n} ngày gần nhất:*\n\n"
    msg += "*Đầu:*\n"
    for i in range(10):
        msg += f"`{i}` : {dau_count.get(str(i), 0)}  "
        if i == 4: msg += "\n"
    msg += "\n*Đuôi:*\n"
    for i in range(10):
        msg += f"`{i}` : {duoi_count.get(str(i), 0)}  "
        if i == 4: msg += "\n"
    return msg

# ==== BACKUP & RESTORE ====
def backup_files(to_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    os.makedirs(to_dir, exist_ok=True)
    backed = []
    for f in files:
        src = os.path.join(GITHUB_REPO_PATH, f)
        dst = os.path.join(to_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            backed.append(dst)
    return backed

def restore_files(from_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    restored = []
    for f in files:
        src = os.path.join(from_dir, f)
        dst = os.path.join(GITHUB_REPO_PATH, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            restored.append(dst)
    return restored

# ==== MENU CALLBACK ====
# ... (Các hàm menu_callback_handler, all_text_handler, help_handler, error_handler, ... Giữ nguyên như bản bạn gửi, hoặc copy lại nguyên si từ code trên, không cần thay đổi gì lớn, chỉ cần chuẩn hoá lại async/await với Python 3.10+.)

# ... (Các import, hàm menu, hàm tiện ích, config...)

# --- Các handler bắt buộc ---
async def menu_callback_handler(update, context):
    await menu(update, context)

async def all_text_handler(update, context):
    await update.message.reply_text("Bạn hãy chọn chức năng trong menu hoặc gõ /menu.")

async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)

async def help_handler(update, context):
    text = (
        "🤖 *Bot XSMB Phong thủy AI*\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start hoặc /menu - Mở menu chính\n"
        "/help - Xem hướng dẫn\n\n"
        "Chức năng nổi bật:\n"
        "• Dự đoán AI XSMB\n"
        "• Ghép xiên, càng, đảo số\n"
        "• Tra cứu phong thủy ngày\n"
        "• Chốt số, hỗ trợ nhiều chế độ\n"
        "• Thống kê, quản trị, backup, cập nhật model\n"
        "• Nhận góp ý, phản hồi, ủng hộ bot"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.add_error_handler(error_handler)
    logger.info("🤖 BOT XSMB đã chạy thành công!")
    app.run_polling()

if __name__ == "__main__":
    main()ut_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày vào: {out_csv}")
        return df
    else:
        print("Không lấy được dữ liệu ngày nào!")
        return None

# ==== TRAIN MODEL RF ====
def train_rf_model_main():
    try:
        from train_rf_xsmb import train_rf_model
        csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
        train_rf_model(csv_path=csv_path, model_path=model_path)
        return True, "✅ Đã train xong, lưu rf_model_xsmb.pkl."
    except Exception as e:
        return False, f"❌ Lỗi train model: {e}"

# ==== AI DỰ ĐOÁN ====
def predict_xsmb_rf():
    model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(model_path) or not os.path.exists(csv_path):
        return "❌ Model hoặc dữ liệu xsmb.csv chưa có trên server!"
    model = joblib.load(model_path)
    df = pd.read_csv(csv_path)
    n_feature = getattr(model, "n_features_in_", 6)
    n_day = n_feature // 2
    if len(df) < n_day or 'DB' not in df.columns or 'G1' not in df.columns:
        return f"❌ Dữ liệu không đủ ({len(df)} ngày), cần {n_day} ngày gần nhất!"
    features = []
    for i in range(-n_day, 0):
        day = df.iloc[i]
        features += [int(str(day['DB'])[-2:]), int(str(day['G1'])[-2:])]
    X_pred = [features]
    y_pred = model.predict(X_pred)
    return f"🤖 Thần tài dự đoán giải đặc biệt hôm nay (2 số cuối):\n👉 {str(y_pred[0]).zfill(2)}\n(ML: Random Forest)"

# ==== THỐNG KÊ XỔ SỐ CƠ BẢN ====
def thong_ke_xsmb(n=15):
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(csv_path):
        return "❌ Chưa có file xsmb.csv trên server!"
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return f"❌ Không đọc được xsmb.csv: {e}"
    df = df.sort_values("date", ascending=False)
    msg = "📊 *Thống kê kết quả XSMB %d ngày gần nhất:*\n\n" % n
    msg += "`Ngày       Đặc biệt   Giải nhất`\n"
    msg += "`-----------------------------`\n"
    for _, row in df.head(n).iterrows():
        msg += f"`{row['date']}  {str(row['DB']).rjust(7)}   {str(row['G1']).rjust(7)}`\n"
    return msg

def thong_ke_dau_duoi_db(n=30):
    csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
    if not os.path.exists(csv_path):
        return "❌ Chưa có file xsmb.csv trên server!"
    df = pd.read_csv(csv_path)
    df = df.sort_values("date", ascending=False).head(n)
    db_list = df['DB'].astype(str).str.zfill(5)
    dau = db_list.str[0]
    duoi = db_list.str[-1]
    dau_count = dau.value_counts().sort_index()
    duoi_count = duoi.value_counts().sort_index()
    msg = f"🔢 *Thống kê ĐẦU & ĐUÔI Đặc biệt {n} ngày gần nhất:*\n\n"
    msg += "*Đầu:*\n"
    for i in range(10):
        msg += f"`{i}` : {dau_count.get(str(i), 0)}  "
        if i == 4: msg += "\n"
    msg += "\n*Đuôi:*\n"
    for i in range(10):
        msg += f"`{i}` : {duoi_count.get(str(i), 0)}  "
        if i == 4: msg += "\n"
    return msg

# ==== BACKUP & RESTORE ====
def backup_files(to_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    os.makedirs(to_dir, exist_ok=True)
    backed = []
    for f in files:
        src = os.path.join(GITHUB_REPO_PATH, f)
        dst = os.path.join(to_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            backed.append(dst)
    return backed

def restore_files(from_dir="backup"):
    files = ["xsmb.csv", "rf_model_xsmb.pkl"]
    restored = []
    for f in files:
        src = os.path.join(from_dir, f)
        dst = os.path.join(GITHUB_REPO_PATH, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            restored.append(dst)
    return restored

# ==== MENU CALLBACK ====
# ... (Các hàm menu_callback_handler, all_text_handler, help_handler, error_handler, ... Giữ nguyên như bản bạn gửi, hoặc copy lại nguyên si từ code trên, không cần thay đổi gì lớn, chỉ cần chuẩn hoá lại async/await với Python 3.10+.)

# ... (Các import, hàm menu, hàm tiện ích, config...)

# --- Các handler bắt buộc ---
async def menu_callback_handler(update, context):
    await menu(update, context)

async def all_text_handler(update, context):
    await update.message.reply_text("Bạn hãy chọn chức năng trong menu hoặc gõ /menu.")

async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)

async def help_handler(update, context):
    text = (
        "🤖 *Bot XSMB Phong thủy AI*\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start hoặc /menu - Mở menu chính\n"
        "/help - Xem hướng dẫn\n\n"
        "Chức năng nổi bật:\n"
        "• Dự đoán AI XSMB\n"
        "• Ghép xiên, càng, đảo số\n"
        "• Tra cứu phong thủy ngày\n"
        "• Chốt số, hỗ trợ nhiều chế độ\n"
        "• Thống kê, quản trị, backup, cập nhật model\n"
        "• Nhận góp ý, phản hồi, ủng hộ bot"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.add_error_handler(error_handler)
    logger.info("🤖 BOT XSMB đã chạy thành công!")
    app.run_polling()

if __name__ == "__main__":
    main()

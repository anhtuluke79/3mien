import os
import logging
import requests
from bs4 import BeautifulSoup
from itertools import combinations
import random
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import joblib

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, ConversationHandler, filters
)

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_gh_cang = {}
user_xien_data = {}
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
XIEN_TYPE, XIEN_NUMBERS = range(2)

# --- Hàm chuyển ngày dương sang Can Chi ---
def get_can_chi_ngay(year, month, day):
    if month < 3:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    chi = chi_list[(jd + 1) % 12]
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    can = can_list[(jd + 9) % 10]
    return f"{can} {chi}"

def sinh_so_hap_cho_ngay(can_chi_str):
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code:
        return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j:
                ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can,
        "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"),
        "so_menh": so_menh,
        "so_hap_list": so_ghep,
        "so_ghép": sorted(list(ket_qua))
    }

def crawl_xsmn_me():
    url = "https://xsmn.me/lich-su-ket-qua-xsmb.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='tblKQ')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ xsmn.me")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl xsmn.me:", e)
        return None

def crawl_minhngoc():
    url = "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-bac.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='resultmb')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ minhngoc.net.vn")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl minhngoc.net.vn:", e)
        return None

def crawl_xosokt():
    url = "https://xosokt.net/xsmb-xo-so-mien-bac.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('table', class_='bangketqua')
        rows = table.find_all('tr')[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all('td')]
            if cols and len(cols) >= 9:
                data.append(cols[:9])
        df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
        print("✅ Crawl thành công từ xosokt.net")
        return df
    except Exception as e:
        print(f"❌ Lỗi crawl xosokt.net:", e)
        return None

def crawl_lich_su_xsmb(filename="xsmb.csv"):
    for func in [crawl_xsmn_me, crawl_minhngoc, crawl_xosokt]:
        df = func()
        if df is not None and not df.empty:
            if not os.path.exists(filename):
                df.to_csv(filename, index=False)
            else:
                df_old = pd.read_csv(filename)
                df_concat = pd.concat([df, df_old]).drop_duplicates(subset=["Ngày"])
                df_concat = df_concat.sort_values("Ngày", ascending=False)
                df_concat.to_csv(filename, index=False)
            print(f"Đã backup lịch sử XSMB vào {filename}")
            return True
    print("❌ Không crawl được dữ liệu từ bất kỳ nguồn nào!")
    return False

def doc_lich_su_xsmb_csv(filename="xsmb.csv", so_ngay=30):
    try:
        df = pd.read_csv(filename)
        if len(df) > so_ngay:
            df = df.head(so_ngay)
        return df
    except Exception as e:
        return None

def du_doan_ai_with_model(df, model_path='model_rf_loto.pkl'):
    df = df.dropna()
    df['ĐB'] = df['ĐB'].astype(str).str[-2:]
    df['ĐB'] = df['ĐB'].astype(int)
    last7 = df['ĐB'][:7].tolist()
    if len(last7) < 7:
        return ["Không đủ dữ liệu 7 ngày!"]
    if not os.path.exists(model_path):
        return ["Chưa có mô hình AI, cần train trước!"]
    model = joblib.load(model_path)
    probs = model.predict_proba([last7])[0]
    top_idx = probs.argsort()[-3:][::-1]
    ketqua = [f"{model.classes_[i]:02d}" for i in top_idx]
    return ketqua

def get_kqxs_mienbac():
    url = "https://xsmn.mobi/xsmn-mien-bac"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="bkqmienbac")
        if not table:
            return {"error": "Không tìm thấy bảng kết quả"}
        results = {}
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                numbers = ' '.join(col.get_text(strip=True) for col in cols[1:])
                results[label] = numbers
        return results
    except Exception as e:
        return {"error": str(e)}

# ----- Handler PHONG THỦY NGÀY -----
async def phongthuy_ngay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        param = ' '.join(context.args)
        # Nếu dạng YYYY-MM-DD thì chuyển sang can chi, còn lại coi là tên can chi
        can_chi = None
        if '-' in param and len(param.split('-')) == 3:
            y, m, d = map(int, param.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            ngay_str = f"{d:02d}/{m:02d}/{y}"
        else:
            can_chi = param.title().replace('_', ' ').replace('-', ' ')
            ngay_str = f"(Tên Can Chi nhập: {can_chi})"

        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text("Không tra được số hạp cho ngày này!")
            return

        df = doc_lich_su_xsmb_csv("xsmb.csv", 60)
        so_du_doan = du_doan_ai_with_model(df)

        so_ghep = set(sohap_info['so_ghép'])
        so_du_doan_set = set(so_du_doan)
        so_trung = so_ghep.intersection(so_du_doan_set)

        text = (
            f"🔮 Phong thủy ngày {can_chi} {ngay_str}:\n"
            f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
            f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
            f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
            f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
            f"- Bộ số AI dự đoán: {', '.join(so_du_doan)}\n"
        )
        if so_trung:
            text += f"\n🌟 **Số vừa là số ghép, vừa AI dự đoán:** {', '.join(so_trung)}"
        else:
            text += "\nKhông có số trùng giữa AI và bộ số ghép."

        await update.message.reply_text(text)
    except Exception:
        await update.message.reply_text(
            "Cách dùng: /phongthuy_ngay YYYY-MM-DD hoặc /phongthuy_ngay Giáp Tý"
        )

# ------ Các handler cơ bản khác giữ nguyên (start, menu, ghepcang, ghepxien, du_doan_ai, thong_ke_db...) ------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\nGõ /menu để bắt đầu."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Kết quả", callback_data="kqxs"),
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🧠 Dự đoán AI", callback_data="du_doan_ai"),
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
        ]
    ]
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# (Các handler như ghepcang_popup, ghepxien_popup, du_doan_ai, thong_ke_db ... giữ nguyên như main.py cũ)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("phongthuy_ngay", phongthuy_ngay_handler))
    # ... các handler khác giữ nguyên ...
    app.run_polling()

if __name__ == "__main__":
    crawl_lich_su_xsmb()
    main()

import os
import logging
import pandas as pd
import joblib
import requests
from bs4 import BeautifulSoup
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)
from itertools import product, combinations
import csv
from datetime import datetime, timedelta
import re

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ============= CONFIG ============
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= TIỆN ÍCH ============
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0:
        return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

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

def ask_gemini(prompt, api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Bạn chưa cấu hình GEMINI_API_KEY!"
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(f"{url}?key={api_key}", json=data, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Gemini API lỗi: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Lỗi gọi Gemini API: {str(e)}"

# ========== CRAWL XỔ SỐ KẾT QUẢ NHIỀU NGÀY ==========
XSKQ_CONFIG = {
    "bac": {
        "base_url": "https://xosoketqua.com/xo-so-mien-bac-xstd",
        "csv": "xsmb.csv",
    },
    "trung": {
        "base_url": "https://xosoketqua.com/xo-so-mien-trung-xsmt",
        "csv": "xsmt.csv",
    },
    "nam": {
        "base_url": "https://xosoketqua.com/xo-so-mien-nam-xsmn",
        "csv": "xsmn.csv",
    }
}
def crawl_xsketqua_mien_multi(region: str, days: int = 30, progress_callback=None):
    region = region.lower()
    if region not in XSKQ_CONFIG:
        raise ValueError("Miền không hợp lệ. Chọn một trong: 'bac', 'trung', 'nam'.")
    base_url = XSKQ_CONFIG[region]['base_url']
    csv_file = XSKQ_CONFIG[region]['csv']
    rows = []
    if os.path.exists(csv_file):
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.reader(f))
    dates_exist = set(row[0] for row in rows)
    count = 0
    today = datetime.now()
    for i in range(days * 2):
        date = today - timedelta(days=i)
        date_str = date.strftime("%d-%m-%Y")
        if date_str.replace("-", "/") in dates_exist or date_str in dates_exist:
            continue
        if region == "bac":
            url = f"{base_url}/ngay-{date_str}.html"
        else:
            url = f"{base_url}?ngay={date_str}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.select_one('div.title-bangketqua h2, h2.title')
            if title:
                title = title.get_text(strip=True)
                found_date = re.search(r'(\d{2}-\d{2}-\d{4})', title)
                if found_date:
                    actual_date = found_date.group(1)
                else:
                    actual_date = date_str
            else:
                actual_date = date_str
            table = soup.select_one("table.tblKQXS")
            if not table:
                continue
            results = []
            for row in table.select("tr"):
                tds = row.find_all("td", class_="bcls")
                if not tds:
                    continue
                for td in tds:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        results.append(txt)
                    elif " " in txt:
                        results.extend([x for x in txt.split() if x.isdigit()])
            if not results:
                continue
            if actual_date.replace("-", "/") in dates_exist or actual_date in dates_exist:
                continue
            with open(csv_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([actual_date] + results)
            dates_exist.add(actual_date)
            count += 1
            if progress_callback and (count % 2 == 0 or count == days):
                progress_callback(count, days)
            if count >= days:
                break
        except Exception as e:
            print(f"Lỗi crawl {region} {date_str}: {e}")
            continue
    return count

# ========== HANDLER TỪNG LỆNH, CALLBACK, COMMAND ==========

# ========== UPDATE DATA MIỀN (chỉ admin, báo tiến trình) ==========
async def capnhat_xsm_kq_handler_query(query, region: str, region_label: str):
    try:
        import asyncio
        msg = await query.edit_message_text(f"⏳ Đang cập nhật 0/30 ngày {region_label} từ xosoketqua.com...")
        progress = {"last_count": 0}
        def progress_callback(count, total):
            if count != progress["last_count"]:
                try:
                    asyncio.run_coroutine_threadsafe(
                        msg.edit_text(f"⏳ Đang cập nhật {count}/{total} ngày {region_label}..."),
                        asyncio.get_event_loop()
                    )
                    progress["last_count"] = count
                except Exception:
                    pass
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, crawl_xsketqua_mien_multi, region, 30, progress_callback)
        await msg.edit_text(f"✅ Đã cập nhật {result} ngày {region_label}!")
    except Exception as e:
        await query.edit_message_text(f"❌ Lỗi crawl {region_label}: {e}")

# ========== MENU & CALLBACK ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🤖 Dự đoán AI", callback_data="ai_predict"),
            InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("💬 Hỏi Gemini", callback_data="hoi_gemini"),
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("🛠️ Update MB", callback_data="capnhat_xsmb_kq"),
            InlineKeyboardButton("🛠️ Update MT", callback_data="capnhat_xsmt_kq"),
            InlineKeyboardButton("🛠️ Update MN", callback_data="capnhat_xsmn_kq"),
            InlineKeyboardButton("⚙️ Train AI", callback_data="train_model"),
        ])
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ===== Admin update data
    if query.data == "capnhat_xsmb_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "bac", "Miền Bắc")
    elif query.data == "capnhat_xsmt_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "trung", "Miền Trung")
    elif query.data == "capnhat_xsmn_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "nam", "Miền Nam")

    # ====== Train model (admin)
    elif query.data == "train_model":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền train AI!")
            return
        await train_model_handler_query(query)

    # ====== Thống kê (user)
    elif query.data == "thongke":
        await thongke_handler_query(query)
    # ====== Dự đoán AI (user)
    elif query.data == "ai_predict":
        await ai_predict_handler_query(query)
    # ====== Phong thủy ngày
    elif query.data == "phongthuy_ngay":
        await query.edit_message_text("Nhập ngày dương lịch (YYYY-MM-DD):")
        context.user_data['wait_phongthuy_ngay'] = True
    # ====== Ghép xiên
    elif query.data == "ghepxien":
        context.user_data['wait_for_xien_input'] = True
        await query.edit_message_text("Nhập dãy số (cách nhau dấu cách, phẩy) để ghép xiên:")
    # ====== Ghép càng
    elif query.data == "ghepcang":
        context.user_data['wait_for_cang_input'] = True
        await query.edit_message_text("Nhập dãy số để ghép càng:")
    # ====== Hỏi Gemini
    elif query.data == "hoi_gemini":
        context.user_data['wait_hoi_gemini'] = True
        await query.edit_message_text("Nhập câu hỏi cho Gemini:")

    else:
        await query.edit_message_text("Chức năng này đang phát triển.")

# ========== ALL TEXT HANDLER ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ghép xiên
    if context.user_data.get('wait_for_xien_input'):
        text = update.message.text.strip()
        numbers = split_numbers(text)
        bo_xien = ghep_xien(numbers, 2)
        await update.message.reply_text(','.join(bo_xien) if bo_xien else "Không ghép được xiên.")
        context.user_data['wait_for_xien_input'] = False
        return

    # Ghép càng
    if context.user_data.get('wait_for_cang_input'):
        text = update.message.text.strip()
        numbers = split_numbers(text)
        bo_so = ghep_cang(numbers, 3)
        await update.message.reply_text(','.join(bo_so) if bo_so else "Không ghép được càng.")
        context.user_data['wait_for_cang_input'] = False
        return

    # Hỏi Gemini
    if context.user_data.get('wait_hoi_gemini'):
        question = update.message.text.strip()
        answer = ask_gemini(question)
        await update.message.reply_text(answer)
        context.user_data['wait_hoi_gemini'] = False
        return

    # Phong thủy ngày
    if context.user_data.get('wait_phongthuy_ngay'):
        ngay = update.message.text.strip()
        try:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if not sohap_info:
                await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
                return
            so_ghep = set(sohap_info['so_ghép'])
            text = (
                f"🔮 Phong thủy ngày {can_chi} ({d:02d}/{m:02d}/{y}):\n"
                f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
                f"- Số mệnh: {sohap_info['so_menh']}\n"
                f"- Số hạp: {', '.join(sohap_info['so_hap_list'])}\n"
                f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}"
            )
            await update.message.reply_text(text)
        except Exception:
            await update.message.reply_text("Nhập ngày không hợp lệ! Đúng định dạng YYYY-MM-DD.")
        context.user_data['wait_phongthuy_ngay'] = False
        return

    # Mặc định
    await update.message.reply_text("Bot đã nhận tin nhắn của bạn!")

# ========== HANDLER: THỐNG KÊ, AI, TRAIN MODEL ==========
async def thongke_handler_query(query):
    try:
        df = pd.read_csv('xsmb.csv')
        dbs = df['ĐB'].astype(str).str[-2:]
        counts = dbs.value_counts().head(10)
        top_list = "\n".join([f"Số {i}: {v} lần" for i, v in counts.items()])
        today_db = dbs.iloc[0] if len(dbs) > 0 else "?"
        text = (
            f"📈 Top 10 số ĐB xuất hiện nhiều nhất 30 ngày gần nhất:\n{top_list}\n"
            f"\n🎯 Số ĐB hôm nay: {today_db}"
        )
        await query.edit_message_text(text)
    except Exception as e:
        await query.edit_message_text(f"Lỗi thống kê: {e}")

async def ai_predict_handler_query(query):
    try:
        df = pd.read_csv('xsmb.csv')
        df = df.dropna()
        df['ĐB'] = df['ĐB'].astype(str).str[-2:]
        df['ĐB'] = df['ĐB'].astype(int)
        if not os.path.exists('model_rf_loto.pkl'):
            await query.edit_message_text("Chưa có mô hình AI, cần train trước!")
            return
        model = joblib.load('model_rf_loto.pkl')
        last7 = df['ĐB'][:7].tolist()
        if len(last7) < 7:
            await query.edit_message_text("Không đủ dữ liệu 7 ngày để dự đoán!")
            return
        probs = model.predict_proba([last7])[0]
        top_idx = probs.argsort()[-3:][::-1]
        ketqua = [f"{model.classes_[i]:02d}" for i in top_idx]
        await query.edit_message_text(
            "🤖 Dự đoán AI (RandomForest) cho lần quay tiếp theo:\n"
            f"Top 3 số: {', '.join(ketqua)}"
        )
    except Exception as e:
        await query.edit_message_text(f"Lỗi AI: {e}")

async def train_model_handler_query(query):
    try:
        await query.edit_message_text("⏳ Đang train lại AI, vui lòng đợi...")
        df = pd.read_csv('xsmb.csv')
        df = df.dropna()
        df['ĐB'] = df['ĐB'].astype(str).str[-2:]
        df['ĐB'] = df['ĐB'].astype(int)
        X, y = [], []
        for i in range(len(df) - 7):
            features = df['ĐB'][i:i+7].tolist()
            label = df['ĐB'][i+7]
            X.append(features)
            y.append(label)
        from sklearn.ensemble import RandomForestClassifier
        import joblib
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        joblib.dump(model, 'model_rf_loto.pkl')
        await query.edit_message_text("✅ Đã train lại và lưu mô hình thành công!")
    except Exception as e:
        await query.edit_message_text(f"Lỗi khi train mô hình: {e}")

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import logging
import pandas as pd
import joblib
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from itertools import product, combinations

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ==== CẤU HÌNH ADMIN (điền user_id Telegram của bạn tại đây) ====
ADMIN_IDS = [12345678]  # Đổi số này thành user_id của bạn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

def ask_gemini(prompt, api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Bạn chưa cấu hình GEMINI_API_KEY!"
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        res = requests.post(
            f"{url}?key={api_key}",
            json=data,
            headers=headers,
            timeout=30
        )
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Gemini API lỗi: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Lỗi gọi Gemini API: {str(e)}"

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

def doc_lich_su_xsmb_csv(filename="xsmb.csv", so_ngay=30):
    try:
        df = pd.read_csv(filename)
        if len(df) > so_ngay:
            df = df.head(so_ngay)
        return df
    except Exception as e:
        logger.warning(f"Lỗi đọc file xsmb.csv: {e}")
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

# --- Crawl dữ liệu XSMB từ web vào xsmb.csv ---
def crawl_xsmn_me():
    url = "https://xsmn.me/lich-su-ket-qua-xsmb.html"
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
    return df

def crawl_lich_su_xsmb(filename="xsmb.csv"):
    df = crawl_xsmn_me()
    if df is not None and not df.empty:
        if not os.path.exists(filename):
            df.to_csv(filename, index=False)
        else:
            df_old = pd.read_csv(filename)
            df_concat = pd.concat([df, df_old]).drop_duplicates(subset=["Ngày"])
            df_concat = df_concat.sort_values("Ngày", ascending=False)
            df_concat.to_csv(filename, index=False)
        return True
    return False

# === GHÉP CÀNG ===
def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0:
        return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

async def ghepcang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args:
            await update.message.reply_text(
                "Cách dùng: /ghepcang 3 1 2 5\n"
                "Ví dụ: /ghepcang 3 1 2 5 sẽ trả về các bộ số 3 càng từ các số 1,2,5.\n"
                "Hoặc: /ghepcang 4 3 8 sẽ trả về các bộ số 4 càng từ 3 và 8."
            )
            return
        try:
            so_cang = int(args[0])
            if so_cang not in [3, 4]:
                raise ValueError
            numbers = [str(int(x)) for x in args[1:]]
        except Exception:
            await update.message.reply_text("Cách dùng: /ghepcang <3|4> <dãy số>\nVí dụ: /ghepcang 3 1 2 5")
            return
        if not numbers:
            await update.message.reply_text("Bạn cần nhập các số để ghép!")
            return
        bo_so = ghep_cang(numbers, so_cang)
        if len(bo_so) > 100:
            bo_so = bo_so[:100]
            tail = "\n...(cắt bớt, hiển thị 100 bộ số đầu)"
        else:
            tail = ""
        await update.message.reply_text(
            f"🎯 Có {len(bo_so)} bộ {so_cang} càng được ghép từ {' '.join(numbers)}:\n"
            + ', '.join(bo_so) + tail
        )
    except Exception as e:
        await update.message.reply_text(f"Lỗi ghép càng: {e}")

# === GHÉP XIÊN ===
def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['-'.join(comb) for comb in result]

async def ghepxien_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args or len(args) < 2:
            await update.message.reply_text(
                "Cách dùng: /ghepxien <2|3|4> <dãy số>\n"
                "Ví dụ: /ghepxien 2 03 15 27 88 sẽ trả về các xiên 2 từ 03, 15, 27, 88."
            )
            return
        try:
            do_dai = int(args[0])
            if do_dai not in [2, 3, 4]:
                raise ValueError
            numbers = [str(int(x)) if x.isdigit() else x for x in args[1:]]
        except Exception:
            await update.message.reply_text("Cách dùng: /ghepxien <2|3|4> <dãy số>\nVí dụ: /ghepxien 2 03 15 88")
            return
        if len(numbers) < do_dai:
            await update.message.reply_text("Bạn cần nhập đủ số để ghép!")
            return
        bo_xien = ghep_xien(numbers, do_dai)
        if len(bo_xien) > 100:
            bo_xien = bo_xien[:100]
            tail = "\n...(cắt bớt, hiển thị 100 bộ đầu)"
        else:
            tail = ""
        await update.message.reply_text(
            f"➕ Có {len(bo_xien)} bộ xiên {do_dai} từ {' '.join(numbers)}:\n"
            + ', '.join(bo_xien) + tail
        )
    except Exception as e:
        await update.message.reply_text(f"Lỗi ghép xiên: {e}")

# === THỐNG KÊ ===
async def thongke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        df = pd.read_csv('xsmb.csv')
        if 'ĐB' not in df.columns or df['ĐB'].isnull().all():
            await update.message.reply_text("Không có dữ liệu ĐB trong xsmb.csv.")
            return
        dbs = df['ĐB'].astype(str).str[-2:]
        counts = dbs.value_counts().head(10)
        top_list = "\n".join([f"Số {i}: {v} lần" for i, v in counts.items()])
        today_db = dbs.iloc[0] if len(dbs) > 0 else "?"
        text = (
            f"📈 Top 10 số ĐB xuất hiện nhiều nhất 30 ngày gần nhất:\n{top_list}\n"
            f"\n🎯 Số ĐB hôm nay: {today_db}"
        )
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Lỗi thống kê: {e}")

# --- Handler: Phong thủy ngày ---
async def phongthuy_ngay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        param = ' '.join(context.args)
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

# --- Handler: Hỏi Gemini ---
async def hoi_gemini_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Bạn hãy nhập câu hỏi sau lệnh /hoi_gemini nhé!")
        return
    answer = ask_gemini(question)
    await update.message.reply_text(answer)

# --- Handler: Train lại AI ---
async def train_model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bạn không có quyền train lại mô hình!")
        return
    try:
        await update.message.reply_text("⏳ Đang train lại AI, vui lòng đợi...")
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
        await update.message.reply_text("✅ Đã train lại và lưu mô hình thành công!")
    except Exception as e:
        await update.message.reply_text(f"Lỗi khi train mô hình: {e}")

# --- Handler: Cập nhật dữ liệu XSMB ---
async def capnhat_xsmb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bạn không có quyền cập nhật dữ liệu!")
        return
    try:
        ok = crawl_lich_su_xsmb("xsmb.csv")
        if ok:
            await update.message.reply_text("✅ Đã cập nhật dữ liệu xsmb.csv thành công!")
        else:
            await update.message.reply_text("❌ Không lấy được dữ liệu mới, vui lòng thử lại sau.")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi cập nhật: {e}")

# --- MENU ---
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🧠 Dự đoán AI", callback_data="du_doan_ai"),
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            InlineKeyboardButton("💬 Hỏi Thần tài", callback_data="hoi_gemini"),
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("⚙️ Train lại AI", callback_data="train_model"),
            InlineKeyboardButton("🛠️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
        ])
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "thongke":
        try:
            df = pd.read_csv('xsmb.csv')
            if 'ĐB' not in df.columns or df['ĐB'].isnull().all():
                await query.edit_message_text("Không có dữ liệu ĐB trong xsmb.csv.")
                return
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
    elif query.data == "ghepcang":
        await query.edit_message_text(
            "🎯 Ghép càng: Bạn hãy gửi lệnh\n"
            "/ghepcang <3|4> <dãy số>\n"
            "Ví dụ: /ghepcang 3 1 2 5 hoặc /ghepcang 4 3 8"
        )
    elif query.data == "ghepxien":
        await query.edit_message_text(
            "➕ Ghép xiên: Bạn hãy gửi lệnh\n"
            "/ghepxien <2|3|4> <dãy số>\n"
            "Ví dụ: /ghepxien 2 03 15 88 hoặc /ghepxien 3 12 23 34 45"
        )
    elif query.data == "train_model":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền train lại mô hình!")
            return
        await query.edit_message_text("⏳ Đang train lại AI, vui lòng đợi...")
        try:
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
    elif query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        try:
            ok = crawl_lich_su_xsmb("xsmb.csv")
            if ok:
                await query.edit_message_text("✅ Đã cập nhật dữ liệu xsmb.csv thành công!")
            else:
                await query.edit_message_text("❌ Không lấy được dữ liệu mới, vui lòng thử lại sau.")
        except Exception as e:
            await query.edit_message_text(f"❌ Lỗi cập nhật: {e}")
    else:
        await query.edit_message_text("Chức năng đang phát triển. Vui lòng sử dụng các lệnh chính.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• /phongthuy_ngay YYYY-MM-DD hoặc /phongthuy_ngay <can chi>\n"
        "• /hoi_gemini <câu hỏi phong thủy/xổ số>\n"
        "• /ghepcang <3|4> <dãy số>\n"
        "• /ghepxien <2|3|4> <dãy số>\n"
        "Chúc bạn may mắn và chơi vui!"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("phongthuy_ngay", phongthuy_ngay_handler))
    app.add_handler(CommandHandler("hoi_gemini", hoi_gemini_handler))
    app.add_handler(CommandHandler("train_model", train_model_handler))
    app.add_handler(CommandHandler("capnhat_xsmb", capnhat_xsmb_handler))
    app.add_handler(CommandHandler("ghepcang", ghepcang_handler))
    app.add_handler(CommandHandler("ghepxien", ghepxien_handler))
    app.add_handler(CommandHandler("thongke", thongke_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

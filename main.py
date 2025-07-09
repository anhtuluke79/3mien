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
    ConversationHandler, MessageHandler, filters
)
from itertools import product, combinations

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

ADMIN_IDS = [12345678]  # Đổi số này thành user_id Telegram của bạn

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
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(f"{url}?key={api_key}", json=data, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Gemini API lỗi: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Lỗi gọi Gemini API: {str(e)}"

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

# === Handler cho ghép càng (ConversationHandler) ===
GHEP_CANG_TYPE, GHEP_CANG_INPUT = range(2)
async def ghepcang_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("3 càng", callback_data="3"), InlineKeyboardButton("4 càng", callback_data="4")]]
    await update.message.reply_text("Bạn muốn ghép càng dạng nào?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GHEP_CANG_TYPE

async def ghepcang_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    so_cang = int(query.data)
    context.user_data['so_cang'] = so_cang
    if so_cang == 3:
        await query.edit_message_text("Nhập dãy số để ghép 3 càng (dấu cách hoặc phẩy):")
    else:
        await query.edit_message_text("Nhập số càng (cách nhau bởi dấu cách hoặc phẩy), sau đó ghi 'ghép' và 3 số để ghép.\nVí dụ: 1 2 3 4 ghép 234")
    return GHEP_CANG_INPUT

async def ghepcang_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    so_cang = context.user_data['so_cang']
    text = update.message.text.strip()
    if so_cang == 3:
        numbers = split_numbers(text)
        if not numbers:
            await update.message.reply_text("Bạn cần nhập các số để ghép!")
            return GHEP_CANG_INPUT
        bo_so = ghep_cang(numbers, 3)
        if len(bo_so) > 100:
            bo_so = bo_so[:100]
        await update.message.reply_text(','.join(bo_so))
    else:
        if 'ghép' not in text:
            await update.message.reply_text("Nhập đúng cú pháp: <càng> ghép <3 số>")
            return GHEP_CANG_INPUT
        parts = text.split('ghép')
        cangs = split_numbers(parts[0])
        so_3d = ''.join(split_numbers(parts[1]))
        if not cangs or len(so_3d) != 3:
            await update.message.reply_text("Nhập đúng cú pháp: <càng> ghép <3 số>")
            return GHEP_CANG_INPUT
        bo_so = [c + so_3d for c in cangs]
        await update.message.reply_text(','.join(bo_so))
    return ConversationHandler.END

ghepcang_conv = ConversationHandler(
    entry_points=[CommandHandler("ghepcang", ghepcang_start)],
    states={
        GHEP_CANG_TYPE: [CallbackQueryHandler(ghepcang_type)],
        GHEP_CANG_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_input)],
    },
    fallbacks=[],
)

# === Handler cho ghép xiên (ConversationHandler) ===
GHEP_XIEN_TYPE, GHEP_XIEN_INPUT = range(2)
async def ghepxien_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Xiên 2", callback_data="2"),
            InlineKeyboardButton("Xiên 3", callback_data="3"),
            InlineKeyboardButton("Xiên 4", callback_data="4"),
        ]
    ]
    await update.message.reply_text("Bạn muốn ghép xiên mấy số?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GHEP_XIEN_TYPE

async def ghepxien_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    do_dai = int(query.data)
    context.user_data['do_dai'] = do_dai
    await query.edit_message_text(f"Nhập dãy số (cách nhau bởi dấu cách hoặc phẩy) để ghép xiên {do_dai}:")
    return GHEP_XIEN_INPUT

async def ghepxien_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    do_dai = context.user_data['do_dai']
    text = update.message.text.strip()
    numbers = split_numbers(text)
    if len(numbers) < do_dai:
        await update.message.reply_text(f"Bạn cần nhập ít nhất {do_dai} số!")
        return GHEP_XIEN_INPUT
    bo_xien = ghep_xien(numbers, do_dai)
    if len(bo_xien) > 100:
        bo_xien = bo_xien[:100]
    await update.message.reply_text(','.join(bo_xien))
    return ConversationHandler.END

ghepxien_conv = ConversationHandler(
    entry_points=[CommandHandler("ghepxien", ghepxien_start)],
    states={
        GHEP_XIEN_TYPE: [CallbackQueryHandler(ghepxien_type)],
        GHEP_XIEN_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_input)],
    },
    fallbacks=[],
)

# --- Handler thống kê ---
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

# --- Handler phong thủy ngày ---
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

# --- Handler hỏi Gemini ---
async def hoi_gemini_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Bạn hãy nhập câu hỏi sau lệnh /hoi_gemini nhé!")
        return
    answer = ask_gemini(question)
    await update.message.reply_text(answer)

# --- Handler train lại AI (admin) ---
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

# --- Handler cập nhật dữ liệu XSMB (admin) ---
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

# --- Callback menu (chỉ thống kê, ghép càng, ghép xiên dùng ConversationHandler, các mục khác là placeholder) ---
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "train_model":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền train lại mô hình!")
            return
        await query.edit_message_text("Gõ /train_model để train lại AI.")
    elif query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await query.edit_message_text("Gõ /capnhat_xsmb để cập nhật dữ liệu xsmb.")
    elif query.data == "thongke":
        await query.edit_message_text("Gõ /thongke để xem thống kê.")
    elif query.data == "phongthuy_ngay":
        await query.edit_message_text("Gõ /phongthuy_ngay <yyyy-mm-dd> hoặc /phongthuy_ngay <can chi> để xem phong thủy.")
    elif query.data == "hoi_gemini":
        await query.edit_message_text("Gõ /hoi_gemini <câu hỏi> để hỏi Thần tài.")
    elif query.data == "du_doan_ai":
        await query.edit_message_text("Tính năng dự đoán AI tích hợp vào các lệnh khác như /phongthuy_ngay.")
    elif query.data == "ghepcang":
        await query.edit_message_text("Gõ /ghepcang để bắt đầu ghép càng.")
    elif query.data == "ghepxien":
        await query.edit_message_text("Gõ /ghepxien để bắt đầu ghép xiên.")
    else:
        await query.edit_message_text("Chức năng đang phát triển.")

# --- Menu ---
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

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• /phongthuy_ngay YYYY-MM-DD hoặc /phongthuy_ngay <can chi>\n"
        "• /hoi_gemini <câu hỏi phong thủy/xổ số>\n"
        "• /ghepcang để ghép càng\n"
        "• /ghepxien để ghép xiên\n"
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
    app.add_handler(CommandHandler("thongke", thongke_handler))
    app.add_handler(ghepcang_conv)
    app.add_handler(ghepxien_conv)
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

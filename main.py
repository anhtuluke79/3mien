import os
import logging
import pandas as pd
import joblib
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)
from itertools import product, combinations
import datetime
import re

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# LẤY ADMIN TỪ BIẾN MÔI TRƯỜNG
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== HỎI GEMINI AI ====
def ask_gemini(prompt, api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Bạn chưa cấu hình GEMINI_API_KEY!"
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
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

# ==== TIỆN ÍCH GHÉP SỐ, PHONG THỦY, CAN CHI ====
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

# ==== CRAWL VÀ CẬP NHẬT XSMB 60 NGÀY (KHÔNG TRÙNG LẶP) ====
def crawl_xsmb_one_day(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="table-kq-xsmb")
    if not table:
        raise Exception("Không tìm thấy bảng kết quả!")
    caption = table.find("caption")
    date_text = caption.get_text(strip=True) if caption else "Không rõ ngày"
    match = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
    date = match.group(1) if match else date_text
    result = {"Ngày": date}
    rows = table.find_all("tr")
    for row in rows:
        th = row.find("th")
        if th:
            ten_giai = th.get_text(strip=True)
            numbers = [td.get_text(strip=True) for td in row.find_all("td")]
            result[ten_giai] = ", ".join(numbers)
    return result

def get_latest_date_in_csv(filename):
    if not os.path.exists(filename):
        return None
    df = pd.read_csv(filename, encoding="utf-8-sig")
    df = df.dropna(subset=["Ngày"])
    df["Ngày_sort"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    latest = df["Ngày_sort"].max()
    return latest

def crawl_new_days_csv(filename="xsmb_full.csv", max_pages=60):
    latest_date = get_latest_date_in_csv(filename)
    print(f"Ngày mới nhất đã có trong file: {latest_date.strftime('%d/%m/%Y') if latest_date else 'Chưa có dữ liệu'}")
    base_url = "https://xoso.com.vn/xo-so-mien-bac/xsmb-p{}.html"
    new_results = []
    for i in range(1, max_pages + 1):
        url = base_url.format(i)
        try:
            kq = crawl_xsmb_one_day(url)
            try:
                date_obj = datetime.datetime.strptime(kq["Ngày"], "%d/%m/%Y")
            except:
                print(f"Lỗi định dạng ngày: {kq['Ngày']} tại trang {url}")
                continue
            if latest_date and date_obj <= latest_date:
                print(f"Đã đến ngày cũ ({kq['Ngày']}), dừng crawl.")
                break
            print(f"Lấy mới ngày: {kq['Ngày']}")
            new_results.append(kq)
        except Exception as e:
            print(f"Lỗi ở trang {url}: {e}")
    if not new_results:
        print("Không có dữ liệu mới cần cập nhật.")
        return
    df_new = pd.DataFrame(new_results)
    if os.path.exists(filename):
        df_old = pd.read_csv(filename, encoding="utf-8-sig")
        df_full = pd.concat([df_new, df_old], ignore_index=True)
        df_full = df_full.drop_duplicates(subset=["Ngày"], keep="first")
    else:
        df_full = df_new
    df_full["Ngày_sort"] = pd.to_datetime(df_full["Ngày"], format="%d/%m/%Y", errors="coerce")
    df_full = df_full.sort_values("Ngày_sort", ascending=False).drop("Ngày_sort", axis=1)
    df_full.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Đã cập nhật {len(df_new)} ngày mới vào {filename}")

# ==== BOT TELEGRAM HANDLER ==== 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
    )

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
            InlineKeyboardButton("⚙️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
            InlineKeyboardButton("⚙️ Train lại AI", callback_data="train_model"),
        ])
    await update.message.reply_text(
        "🔹 Chọn chức năng:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ==== Cập nhật XSMB (admin) ====
    if query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await query.edit_message_text("⏳ Đang cập nhật dữ liệu xsmb_full.csv (60 ngày)...")
        import asyncio
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, crawl_new_days_csv, 'xsmb_full.csv', 60)
        await query.edit_message_text("✅ Đã cập nhật dữ liệu xsmb_full.csv thành công (60 ngày mới nhất)!")
        return

    # ==== Thống kê ====
    if query.data == "thongke":
        try:
            df = pd.read_csv('xsmb_full.csv')
            if 'Đặc biệt' not in df.columns or df['Đặc biệt'].isnull().all():
                await query.edit_message_text("Không có dữ liệu ĐB trong xsmb_full.csv.")
                return
            dbs = df['Đặc biệt'].astype(str).str[-2:]
            counts = dbs.value_counts().head(10)
            top_list = "\n".join([f"Số {i}: {v} lần" for i, v in counts.items()])
            today_db = dbs.iloc[0] if len(dbs) > 0 else "?"
            text = (
                f"📈 Top 10 số ĐB xuất hiện nhiều nhất 60 ngày gần nhất:\n{top_list}\n"
                f"\n🎯 Số ĐB hôm nay: {today_db}"
            )
            await query.edit_message_text(text)
        except Exception as e:
            await query.edit_message_text(f"Lỗi thống kê: {e}")
        return

    # ==== Dự đoán AI ====
    if query.data == "du_doan_ai":
        try:
            df = pd.read_csv('xsmb_full.csv')
            df = df.dropna()
            df['Đặc biệt'] = df['Đặc biệt'].astype(str).str[-2:]
            df['Đặc biệt'] = df['Đặc biệt'].astype(int)
            if not os.path.exists('model_rf_loto.pkl'):
                await query.edit_message_text("Chưa có mô hình AI, cần train trước bằng lệnh /train_model.")
                return
            model = joblib.load('model_rf_loto.pkl')
            last7 = df['Đặc biệt'][:7].tolist()
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
            await query.edit_message_text(f"Lỗi dự đoán AI: {e}")
        return

    # ==== Ghép xiên / Ghép càng ====
    if query.data == "ghepxien":
        keyboard = [
            [
                InlineKeyboardButton("Xiên 2", callback_data="ghepxien_2"),
                InlineKeyboardButton("Xiên 3", callback_data="ghepxien_3"),
                InlineKeyboardButton("Xiên 4", callback_data="ghepxien_4"),
            ]
        ]
        await query.edit_message_text("Chọn dạng ghép xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data.startswith("ghepxien_"):
        do_dai = int(query.data.split("_")[1])
        context.user_data['do_dai'] = do_dai
        context.user_data['wait_for_xien_input'] = True
        await query.edit_message_text(
            f"Nhập dãy số (cách nhau bởi dấu cách hoặc phẩy) để ghép xiên {do_dai}:"
        )
        return
    if query.data == "ghepcang":
        keyboard = [
            [
                InlineKeyboardButton("3 càng", callback_data="ghepcang_3"),
                InlineKeyboardButton("4 càng", callback_data="ghepcang_4"),
            ]
        ]
        await query.edit_message_text("Chọn dạng ghép càng:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data.startswith("ghepcang_"):
        so_cang = int(query.data.split("_")[1])
        context.user_data['so_cang'] = so_cang
        context.user_data['wait_for_cang_input'] = True
        if so_cang == 3:
            await query.edit_message_text("Nhập dãy số để ghép 3 càng (dấu cách hoặc phẩy):")
        else:
            await query.edit_message_text("Nhập số càng (cách nhau bởi dấu cách hoặc phẩy), sau đó ghi 'ghép' và 3 số để ghép. VD: 1 2 3 4 ghép 234")
        return

    # ==== Phong thủy ngày ====
    if query.data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("Nhập ngày dương (YYYY-MM-DD)", callback_data="ptn_ngay_duong")],
            [InlineKeyboardButton("Nhập can chi (ví dụ: Giáp Tý)", callback_data="ptn_can_chi")]
        ]
        await query.edit_message_text("Bạn muốn tra phong thủy theo kiểu nào?", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data == "ptn_ngay_duong":
        await query.edit_message_text("Nhập ngày dương lịch (YYYY-MM-DD):")
        context.user_data['wait_phongthuy_ngay'] = 'duong'
        return
    if query.data == "ptn_can_chi":
        await query.edit_message_text("Nhập can chi (ví dụ: Giáp Tý):")
        context.user_data['wait_phongthuy_ngay'] = 'canchi'
        return

    # ==== Hỏi Gemini ====
    if query.data == "hoi_gemini":
        await query.edit_message_text("Mời bạn nhập câu hỏi muốn hỏi Thần tài:")
        context.user_data['wait_hoi_gemini'] = True
        return

    # ==== Train lại AI (admin) ====
    if query.data == "train_model":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền train lại mô hình!")
            return
        await query.edit_message_text("⏳ Đang train lại AI, vui lòng đợi...")
        try:
            df = pd.read_csv('xsmb_full.csv')
            df = df.dropna()
            df['Đặc biệt'] = df['Đặc biệt'].astype(str).str[-2:]
            df['Đặc biệt'] = df['Đặc biệt'].astype(int)
            X, y = [], []
            for i in range(len(df) - 7):
                features = df['Đặc biệt'][i:i+7].tolist()
                label = df['Đặc biệt'][i+7]
                X.append(features)
                y.append(label)
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            joblib.dump(model, 'model_rf_loto.pkl')
            await query.edit_message_text("✅ Đã train lại và lưu mô hình thành công!")
        except Exception as e:
            await query.edit_message_text(f"Lỗi khi train mô hình: {e}")
        return

    await query.edit_message_text("Chức năng này đang phát triển hoặc chưa được cấu hình!")

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ghép xiên
    if context.user_data.get('wait_for_xien_input'):
        do_dai = context.user_data.get('do_dai')
        text = update.message.text.strip()
        numbers = split_numbers(text)
        if len(numbers) < do_dai:
            await update.message.reply_text(f"Bạn cần nhập ít nhất {do_dai} số!")
            return
        bo_xien = ghep_xien(numbers, do_dai)
        if len(bo_xien) > 100:
            bo_xien = bo_xien[:100]
        await update.message.reply_text(','.join(bo_xien))
        context.user_data['wait_for_xien_input'] = False
        return
    # Ghép càng
    if context.user_data.get('wait_for_cang_input'):
        so_cang = context.user_data.get('so_cang')
        text = update.message.text.strip()
        if so_cang == 3:
            numbers = split_numbers(text)
            if not numbers:
                await update.message.reply_text("Bạn cần nhập các số để ghép!")
                return
            bo_so = ghep_cang(numbers, 3)
            if len(bo_so) > 100:
                bo_so = bo_so[:100]
            await update.message.reply_text(','.join(bo_so))
        else:
            if 'ghép' not in text:
                await update.message.reply_text("Nhập đúng cú pháp: <càng> ghép <3 số>")
                return
            parts = text.split('ghép')
            cangs = split_numbers(parts[0])
            so_3d = ''.join(split_numbers(parts[1]))
            if not cangs or len(so_3d) != 3:
                await update.message.reply_text("Nhập đúng cú pháp: <càng> ghép <3 số>")
                return
            bo_so = [c + so_3d for c in cangs]
            await update.message.reply_text(','.join(bo_so))
        context.user_data['wait_for_cang_input'] = False
        return
    # Hỏi Gemini
    if context.user_data.get('wait_hoi_gemini'):
        question = update.message.text.strip()
        answer = ask_gemini(question)
        await update.message.reply_text(answer)
        context.user_data['wait_hoi_gemini'] = False
        return
    # Phong thủy ngày (nhập ngày dương)
    if context.user_data.get('wait_phongthuy_ngay') == 'duong':
        ngay = update.message.text.strip()
        if "-" in ngay and len(ngay.split('-')) == 3:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            ngay_str = f"{d:02d}/{m:02d}/{y}"
        else:
            await update.message.reply_text("Vui lòng nhập ngày đúng định dạng YYYY-MM-DD.")
            return
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
            return
        so_ghep = set(sohap_info['so_ghép'])
        text = (
            f"🔮 Phong thủy ngày {can_chi} {ngay_str}:\n"
            f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
            f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
            f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
            f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
        )
        await update.message.reply_text(text)
        context.user_data['wait_phongthuy_ngay'] = False
        return
    # Phong thủy ngày (nhập can chi)
    if context.user_data.get('wait_phongthuy_ngay') == 'canchi':
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
            return
        so_ghep = set(sohap_info['so_ghép'])
        text = (
            f"🔮 Phong thủy ngày {can_chi}:\n"
            f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
            f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
            f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
            f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
        )
        await update.message.reply_text(text)
        context.user_data['wait_phongthuy_ngay'] = False
        return

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), all_text_handler))
    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

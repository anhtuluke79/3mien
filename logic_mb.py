import os
import pandas as pd
import joblib
import requests
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH", ".")

# ======= CRAWL XSMB =======
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

# ======= TRAIN MODEL RF =======
def train_rf_model_main():
    try:
        from train_rf_xsmb import train_rf_model
        csv_path = os.path.join(GITHUB_REPO_PATH, "xsmb.csv")
        model_path = os.path.join(GITHUB_REPO_PATH, "rf_model_xsmb.pkl")
        train_rf_model(csv_path=csv_path, model_path=model_path)
        return True, "✅ Đã train xong, lưu rf_model_xsmb.pkl."
    except Exception as e:
        return False, f"❌ Lỗi train model: {e}"

# ======= DỰ ĐOÁN RF =======
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

# ======= THỐNG KÊ CƠ BẢN =======
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

# ======= THỐNG KÊ ĐẦU ĐUÔI =======
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

# ======= TEXT HANDLER (cho telegram) =======
async def xsmb_text_handler(update, context):
    mode = context.user_data.get("mode")
    submode = context.user_data.get("submode", "")
    if mode == "xsmb":
        msg = thong_ke_xsmb(15)
        await update.message.reply_text(msg, parse_mode="Markdown")
        context.user_data["mode"] = None
        return
    if mode == "thongke" and submode == "dauduoi":
        msg = thong_ke_dau_duoi_db(30)
        await update.message.reply_text(msg, parse_mode="Markdown")
        context.user_data["mode"] = None
        context.user_data["submode"] = None
        return
    # Dự đoán RF
    if mode == "ml_predict":
        result = predict_xsmb_rf()
        await update.message.reply_text(result)
        context.user_data["mode"] = None
        return
    # Chưa hỗ trợ mode khác
    await update.message.reply_text("Bạn chọn chức năng thống kê/dự đoán/AI từ menu.")

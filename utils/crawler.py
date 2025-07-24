import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import random
import re

def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
    """Crawl 1 ngày kết quả XSMB từ minhchinh.com"""
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
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
                match = re.search(r'(\d{5})\b', value)
                result["DB"] = match.group(1) if match else value
            elif "Nhất" in label:
                result["G1"] = value
            elif "Nhì" in label:
                result["G2"] = value
            elif "Ba" in label:
                result["G3"] = value
            elif "Tư" in label:
                result["G4"] = value
            elif "Năm" in label:
                result["G5"] = value
            elif "Sáu" in label:
                result["G6"] = value
            elif "Bảy" in label:
                result["G7"] = value
        return result
    except Exception as e:
        print(f"❌ {date_str}: {e}")
        return None

def crawl_xsmb_Nngay_minhchinh_csv(N=60, out_csv="xsmb.csv", delay_sec=6, use_random_delay=True):
    """
    Crawl N ngày XSMB gần nhất, lưu vào file CSV (gộp thêm dữ liệu nếu đã có).
    """
    today = datetime.today()
    if os.path.exists(out_csv):
        df_old = pd.read_csv(out_csv)
        days_have = set(str(d) for d in df_old['date'])
    else:
        df_old = None
        days_have = set()
    records = []
    for i in range(1, N+1):  # Bắt đầu từ hôm qua (i=1)
        date = today - timedelta(days=i)
        date_str = f"{date.year}-{date.month:02d}-{date.day:02d}"
        if date_str in days_have:
            print(f"❎ {date.strftime('%d-%m-%Y')} ĐÃ có trong file, bỏ qua.")
            continue
        row = crawl_xsmb_1ngay_minhchinh_dict(date.day, date.month, date.year)
        if row:
            records.append(row)
            print(f"✔️ {date.strftime('%d-%m-%Y')} OK, đã thêm mới.")
        else:
            print(f"❌ {date.strftime('%d-%m-%Y')} KHÔNG lấy được!")
        if use_random_delay:
            t = random.uniform(delay_sec*0.7, delay_sec*1.3)
            print(f"⏳ Đợi {t:.1f} giây để tránh bị chặn...")
            time.sleep(t)
        else:
            print(f"⏳ Đợi {delay_sec} giây để tránh bị chặn...")
            time.sleep(delay_sec)
    # Gộp dữ liệu cũ và mới
    if records:
        df_new = pd.DataFrame(records)
        if df_old is not None:
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_all = df_new
        df_all = df_all.drop_duplicates(subset="date").sort_values("date", ascending=False)
        df_all.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\nĐã cập nhật file: {out_csv}. Tổng cộng {len(df_all)} ngày.")
        return df_all
    else:
        print("Không có ngày nào mới để cập nhật!")
        return df_old if df_old is not None else None

# --- OPTIONAL: Hàm upload lên Google Drive (chỉ dùng cho Colab, không import mặc định) ---
def upload_csv_to_drive(local_path, remote_name=None, parent_folder_id=None):
    try:
        from pydrive.auth import GoogleAuth
        from pydrive.drive import GoogleDrive
        from google.colab import auth
        from oauth2client.client import GoogleCredentials

        auth.authenticate_user()
        gauth = GoogleAuth()
        gauth.credentials = GoogleCredentials.get_application_default()
        drive = GoogleDrive(gauth)
        if remote_name is None:
            remote_name = os.path.basename(local_path)
        file_drive = drive.CreateFile({
            'title': remote_name,
            'parents': [{"id": parent_folder_id}] if parent_folder_id else []
        })
        file_drive.SetContentFile(local_path)
        file_drive.Upload()
        print(f"✅ Đã upload {local_path} lên Google Drive (tên trên Drive: {remote_name})")
        print(f"👉 Link file: https://drive.google.com/file/d/{file_drive['id']}/view?usp=sharing")
    except Exception as e:
        print(f"❌ Lỗi upload lên Drive: {e}")

# --- Main entry chạy độc lập ---
if __name__ == "__main__":
    csv_path = "xsmb.csv"
    crawl_xsmb_Nngay_minhchinh_csv(60, csv_path, delay_sec=6, use_random_delay=True)
    # Nếu chạy trên Colab và muốn upload:
    try:
        import google.colab
        parent_folder_id = "YOUR_DRIVE_FOLDER_ID"
        upload_csv_to_drive(csv_path, "xsmb.csv", parent_folder_id)
    except ImportError:
        print("Not running in Colab: Skip Google Drive upload.")

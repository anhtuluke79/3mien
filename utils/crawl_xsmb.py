import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def crawl_xsmb_1ngay_minhchinh_dict(ngay, thang, nam):
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
                result["DB"] = value
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

def crawl_xsmb_Nngay_minhchinh_csv(N=60, out_csv="xsmb.csv"):
    """
    Crawl N ngày gần nhất (bỏ ngày hôm nay), chỉ thêm ngày mới chưa có vào file CSV.
    """
    today = datetime.today()
    # Đọc file hiện tại nếu có
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
        time.sleep(1)
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

# --- Chạy thử ---
if __name__ == "__main__":
    crawl_xsmb_Nngay_minhchinh_csv(60, "xsmb.csv")

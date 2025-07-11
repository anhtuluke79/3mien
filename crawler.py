import os
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
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
            res = requests.get(url, timeout=10, headers=headers)
            print(f"DEBUG: {url} => status {res.status_code}")
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.select_one("table.tblKQXS")
            if not table:
                print("Không tìm thấy bảng kết quả!")
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
            with open(csv_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([date_str] + results)
            dates_exist.add(date_str)
            count += 1
            if progress_callback and (count % 2 == 0 or count == days):
                progress_callback(count, days)
            if count >= days:
                break
        except Exception as e:
            print(f"Lỗi crawl {region} {date_str}: {e}")
            continue
    return count

# Nếu chạy riêng file này sẽ crawl thử 3 ngày miền Bắc
if __name__ == "__main__":
    n = crawl_xsketqua_mien_multi('bac', days=3)
    print(f"Cập nhật {n} ngày mới miền Bắc!")


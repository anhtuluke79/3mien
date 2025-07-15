import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from itertools import combinations, product

from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0: return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

def get_can_chi_ngay(year, month, day):
    if month < 3: year -= 1; month += 12
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
        "can": can,
        "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"),
        "so_menh": so_menh,
        "so_hap_list": so_ghep,
        "so_ghép": sorted(list(ket_qua))
    }

def crawl_xsmn_mobi():
    url = "https://xsmn.mobi/ket-qua-xo-so-mien-bac/lich-su"
    r = requests.get(url, timeout=10, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find('table', class_='table-xs')
    if table is None:
        raise Exception("Không tìm thấy bảng kết quả trên xsmn.mobi.")
    rows = table.find_all('tr')[1:]
    data = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all('td')]
        if cols and len(cols) >= 9:
            data.append(cols[:9])
    df = pd.DataFrame(data, columns=['Ngày', 'ĐB', '1', '2', '3', '4', '5', '6', '7'])
    return df

def crawl_lich_su_xsmb(filename="xsmb.csv"):
    try:
        df = crawl_xsmn_mobi()
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
    except Exception as e:
        print(f"Lỗi crawl xsmn.mobi: {e}")
        return False

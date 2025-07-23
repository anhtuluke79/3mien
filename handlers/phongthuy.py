import pandas as pd
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def tra_can_theo_nam(nam):
    path = os.path.join(ROOT_DIR, "thien_can.csv")
    df = pd.read_csv(path)
    row = df[df['nam'] == int(nam)]
    if not row.empty:
        return row.iloc[0]['can']
    return "?"

def tra_chi_theo_nam(nam):
    path = os.path.join(ROOT_DIR, "can_chi.csv")
    df = pd.read_csv(path)
    idx = (int(nam) - 1984) % 12  # Giả sử 1984 là Giáp Tý, bạn điều chỉnh theo file
    if 0 <= idx < len(df):
        return df.iloc[idx]['chi']
    return "?"

def phongthuy_ngay(ngay_str):
    """
    Trả về thông tin can, chi, số gợi ý... dựa trên ngày nhập.
    """
    # Parse năm từ ngày, ví dụ: 2025-07-24
    try:
        nam = int(str(ngay_str).split("-")[0])
    except:
        return "Không xác định được năm từ ngày nhập."
    can = tra_can_theo_nam(nam)
    chi = tra_chi_theo_nam(nam)
    # Có thể tra tiếp số may mắn, mệnh, màu hợp, ...
    return f"🌟 Năm {nam} là {can} {chi}.\nSố gợi ý: 68, 79."

def phongthuy_can_chi(can_chi_str):
    """
    Truy xuất ý nghĩa hoặc số hợp từ can chi (tra từ file can_chi.csv).
    """
    path = os.path.join(ROOT_DIR, "can_chi.csv")
    df = pd.read_csv(path)
    row = df[df['chi'].str.lower() == can_chi_str.lower()]
    if not row.empty:
        nghia = row.iloc[0]['nghia']
        return f"Can chi {can_chi_str} nghĩa là: {nghia}. Số gợi ý: 86, 39."
    return f"Không tìm thấy can chi {can_chi_str} trong dữ liệu."

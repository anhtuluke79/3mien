import pandas as pd
from collections import Counter

def _tach_dan_so(series):
    # Tách 2 số cuối mỗi số trong chuỗi/Series, trả list tất cả 2 số
    all_numbers = []
    for val in series.dropna():
        s_raw = str(val).replace(" ", ",")
        for s in s_raw.split(","):
            s = s.strip()
            while len(s) >= 2:
                all_numbers.append(s[-2:])  # chỉ lấy 2 số cuối mỗi chuỗi
                s = s[:-2] if len(s) > 2 else ""
    return all_numbers

def soicau_lientuc(df, n=60, min_len=2):
    """Tìm các số xuất hiện liên tiếp >= min_len ngày gần nhất."""
    df = df.sort_values("date", ascending=False).head(n)
    # Lấy các dàn số cho từng ngày
    dan_ngay = []
    for _, row in df.iterrows():
        day_nums = []
        for col in ["DB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]:
            day_nums += _tach_dan_so(pd.Series([row[col]]))
        dan_ngay.append(set(day_nums))
    streaks = Counter()
    for i, today in enumerate(dan_ngay):
        for num in today:
            streak = 1
            for j in range(i+1, len(dan_ngay)):
                if num in dan_ngay[j]:
                    streak += 1
                else:
                    break
            if streak >= min_len:
                streaks[num] = max(streaks[num], streak)
    if not streaks:
        return "*Không có số nào ra liên tục nhiều ngày.*"
    res = "*Số xuất hiện liên tiếp nhiều ngày (60 ngày):*\n"
    res += "\n".join([f"{num}: {cnt} ngày" for num, cnt in streaks.most_common()])
    return res

def soicau_ganmax(df, n=60):
    """Thống kê các số 2 chữ số lâu chưa ra nhất 60 ngày."""
    df = df.sort_values("date", ascending=False).head(n)
    all_2digit = {f"{i:02d}" for i in range(100)}
    gan_dict = {num: 0 for num in all_2digit}
    # Duyệt ngược: mỗi ngày, nếu số chưa ra, +1, nếu ra, reset 0
    for _, row in df.iterrows():
        appeared_today = set()
        for col in ["DB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]:
            appeared_today |= set(_tach_dan_so(pd.Series([row[col]])))
        for num in gan_dict:
            if num not in appeared_today:
                gan_dict[num] += 1
            else:
                gan_dict[num] = 0
    gan_sorted = sorted(gan_dict.items(), key=lambda x: -x[1])
    res = "*Số gan cực đại (lâu chưa ra):*\n"
    res += ", ".join([f"{num}: {cnt} ngày" for num, cnt in gan_sorted[:10] if cnt > 0])
    return res

def soicau_kep(df, n=60):
    """Thống kê số kép (00, 11, ..., 99) 60 ngày gần nhất."""
    df = df.sort_values("date", ascending=False).head(n)
    all_numbers = []
    for col in ["DB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]:
        all_numbers += _tach_dan_so(df[col])
    kep = [num for num in all_numbers if len(num) == 2 and num[0] == num[1]]
    cnt = Counter(kep)
    if not cnt:
        return "*Không có số kép nào trong 60 ngày!*"
    res = "*Thống kê số kép (00, 11, ... 99) trong 60 ngày:*\n"
    res += ", ".join([f"{k}: {v} lần" for k, v in cnt.most_common()])
    return res

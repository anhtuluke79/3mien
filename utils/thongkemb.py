import pandas as pd
import random

def read_xsmb(filename="xsmb.csv"):
    return pd.read_csv(filename)

def tach_dan_so(series):
    """
    Tách các số 2 chữ số từ một Series, dù là dính liền hay cách bằng dấu phẩy, dấu cách.
    """
    all_numbers = []
    for val in series.dropna():
        s_raw = str(val).replace(" ", ",")
        for s in s_raw.split(","):
            s = s.strip()
            # Nếu là số dài, cắt thành các số 2 chữ số
            while len(s) >= 2:
                all_numbers.append(s[:2])
                s = s[2:]
    return all_numbers

def thongke_so_ve_nhieu_nhat(df, n=30, top=10, bot_only=False):
    df = df.sort_values("date", ascending=False).head(n)
    all_numbers = (
        df["DB"].astype(str).tolist()
        + df["G1"].astype(str).tolist()
        + tach_dan_so(df["G2"])
        + tach_dan_so(df["G3"])
        + tach_dan_so(df["G4"])
        + tach_dan_so(df["G5"])
        + tach_dan_so(df["G6"])
        + tach_dan_so(df["G7"])
    )
    counts = pd.Series(all_numbers).value_counts()
    if bot_only:
        counts = counts.tail(top)
        title = f"*📉 Số về ít nhất {n} ngày:*"
    else:
        counts = counts.head(top)
        title = f"*📈 Top số về nhiều nhất {n} ngày:*"
    res = title + "\n"
    res += "\n".join([f"{i+1}. `{num}` — {cnt} lần" for i, (num, cnt) in enumerate(counts.items())])
    return res

def thongke_dau_cuoi(df, n=30):
    df = df.sort_values("date", ascending=False).head(n)
    db = df["DB"].astype(str)
    dau = db.str[0]
    duoi = db.str[-1]
    thongke_dau = dau.value_counts().sort_index()
    thongke_duoi = duoi.value_counts().sort_index()
    res = f"*Thống kê ĐẦU/ĐUÔI giải ĐB {n} ngày:*\n"
    res += "Đầu: " + ', '.join([f"{i}: {thongke_dau.get(str(i),0)}" for i in range(10)]) + "\n"
    res += "Đuôi: " + ', '.join([f"{i}: {thongke_duoi.get(str(i),0)}" for i in range(10)]) + "\n"
    return res

def thongke_chan_le(df, n=30):
    df = df.sort_values("date", ascending=False).head(n)
    db = df["DB"].astype(str)
    chan = sum(int(x[-1]) % 2 == 0 for x in db)
    le = len(db) - chan
    res = f"*Thống kê chẵn/lẻ giải ĐB {n} ngày:*\nChẵn: {chan}, Lẻ: {le}"
    return res

def thongke_lo_gan(df, n=30):
    df = df.sort_values("date", ascending=False).head(n)
    appeared = set(
        df["DB"].astype(str).tolist()
        + df["G1"].astype(str).tolist()
        + tach_dan_so(df["G2"])
        + tach_dan_so(df["G3"])
        + tach_dan_so(df["G4"])
        + tach_dan_so(df["G5"])
        + tach_dan_so(df["G6"])
        + tach_dan_so(df["G7"])
    )
    all_2digit = {f"{i:02d}" for i in range(100)}
    gan = sorted(all_2digit - appeared)
    res = f"*Dàn lô gan (lâu chưa ra trong {n} ngày):*\n"
    res += ", ".join(gan) if gan else "Không có số nào!"
    return res

def goi_y_du_doan(df, n=30):
    top = thongke_so_ve_nhieu_nhat(df, n=n, top=10, bot_only=False)
    lo_gan = thongke_lo_gan(df, n=n)
    dau_cuoi = thongke_dau_cuoi(df, n=n)
    chan_le = thongke_chan_le(df, n=n)
    # Lấy 1–2 số bất kỳ trong top để dự đoán vui
    top_lines = top.split("\n")[1:]
    so_goiy = random.choice(top_lines).split("`")[1] if top_lines else "??"
    res = (
        f"🌟 *Dự đoán vui cho ngày mai:*\n"
        f"Số nổi bật: `{so_goiy}`\n\n"
        f"{top}\n\n"
        f"{lo_gan}\n\n"
        f"{dau_cuoi}\n\n"
        f"{chan_le}\n"
    )
    return res

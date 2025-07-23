import pandas as pd

def read_xsmb(filename="xsmb.csv"):
    return pd.read_csv(filename)

def thongke_so_ve_nhieu_nhat(df, n=30, top=10, bot_only=False):
    df = df.sort_values("date", ascending=False).head(n)
    all_numbers = (
        df["DB"].astype(str).tolist()
        + df["G1"].astype(str).tolist()
        + df["G2"].astype(str).str.split(",").sum()
        + df["G3"].astype(str).str.split(",").sum()
        + df["G4"].astype(str).str.split(",").sum()
        + df["G5"].astype(str).str.split(",").sum()
        + df["G6"].astype(str).str.split(",").sum()
        + df["G7"].astype(str).str.split(",").sum()
    )
    counts = pd.Series(all_numbers).value_counts()
    if bot_only:
        counts = counts.tail(top)
        title = "*📉 Số về ít nhất 30 ngày:*"
    else:
        counts = counts.head(top)
        title = "*📈 Top số về nhiều nhất 30 ngày:*"
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
    res = "*Thống kê ĐẦU/ĐUÔI giải ĐB 30 ngày:*\n"
    res += "Đầu: " + ', '.join([f"{i}: {thongke_dau.get(str(i),0)}" for i in range(10)]) + "\n"
    res += "Đuôi: " + ', '.join([f"{i}: {thongke_duoi.get(str(i),0)}" for i in range(10)]) + "\n"
    return res

def thongke_chan_le(df, n=30):
    df = df.sort_values("date", ascending=False).head(n)
    db = df["DB"].astype(str)
    chan = sum(int(x[-1]) % 2 == 0 for x in db)
    le = len(db) - chan
    res = f"*Thống kê chẵn/lẻ giải ĐB 30 ngày:*\nChẵn: {chan}, Lẻ: {le}"
    return res

def thongke_lo_gan(df, n=30):
    df = df.sort_values("date", ascending=False).head(n)
    appeared = set(
        df["DB"].astype(str).tolist()
        + df["G1"].astype(str).tolist()
        + df["G2"].astype(str).str.split(",").sum()
        + df["G3"].astype(str).str.split(",").sum()
        + df["G4"].astype(str).str.split(",").sum()
        + df["G5"].astype(str).str.split(",").sum()
        + df["G6"].astype(str).str.split(",").sum()
        + df["G7"].astype(str).str.split(",").sum()
    )
    all_2digit = {f"{i:02d}" for i in range(100)}
    gan = sorted(all_2digit - appeared)
    res = "*Dàn lô gan (lâu chưa ra trong 30 ngày):*\n"
    res += ", ".join(gan) if gan else "Không có số nào!"
    return res

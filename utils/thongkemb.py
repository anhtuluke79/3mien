import pandas as pd
import random
from collections import Counter

def read_xsmb(filename="xsmb.csv"):
    return pd.read_csv(filename)

def lay_tat_ca_2so_cuoi(df, n=30):
    """Lấy toàn bộ 2 số cuối của tất cả giải trong n ngày gần nhất"""
    df = df.sort_values("date", ascending=False).head(n)
    numbers = []
    for col in ["DB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]:
        for value in df[col]:
            nums = str(value).replace(",", " ").split()
            for num in nums:
                last2 = num[-2:].zfill(2)
                numbers.append(last2)
    return numbers

def thongke_so_ve_nhieu_nhat(df, n=30, top=10, bot_only=False):
    all_numbers = lay_tat_ca_2so_cuoi(df, n)
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

def thongke_lo_gan(df, n=30):
    all_numbers = set(lay_tat_ca_2so_cuoi(df, n))
    all_2digit = {f"{i:02d}" for i in range(100)}
    gan = sorted(all_2digit - all_numbers)
    res = f"*Dàn lô gan (lâu chưa ra trong {n} ngày):*\n"
    res += ", ".join(gan) if gan else "Không có số nào!"
    return res

def thongke_dau_cuoi(df, n=30):
    """Chỉ thống kê đầu/đuôi của giải ĐB, theo 2 số cuối của mỗi ngày."""
    df = df.sort_values("date", ascending=False).head(n)
    db_numbers = df["DB"].astype(str)
    numbers = [num[-2:].zfill(2) for num in db_numbers]
    dau = [s[0] for s in numbers]
    duoi = [s[1] for s in numbers]
    thongke_dau = Counter(dau)
    thongke_duoi = Counter(duoi)
    res = f"*Thống kê ĐẦU/ĐUÔI giải ĐB {n} ngày (2 số cuối mỗi ngày):*\n"
    res += "Đầu: " + ', '.join([f"{i}: {thongke_dau.get(str(i),0)}" for i in range(10)]) + "\n"
    res += "Đuôi: " + ', '.join([f"{i}: {thongke_duoi.get(str(i),0)}" for i in range(10)]) + "\n"
    return res

def thongke_chan_le(df, n=30):
    """Chỉ thống kê chẵn/lẻ cho giải ĐB, theo 2 số cuối mỗi ngày."""
    df = df.sort_values("date", ascending=False).head(n)
    db_numbers = df["DB"].astype(str)
    numbers = [num[-2:].zfill(2) for num in db_numbers]
    chan = sum(int(s[-1]) % 2 == 0 for s in numbers)
    le = len(numbers) - chan
    res = f"*Thống kê chẵn/lẻ giải ĐB {n} ngày (2 số cuối mỗi ngày):*\nChẵn: {chan}, Lẻ: {le}"
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

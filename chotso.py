from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from can_chi_dict import data as CAN_CHI_DICT
from thien_can import CAN_INFO

CAN_LIST = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
CHI_LIST = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
CAN_CHI_LIST = [f"{can} {chi}" for can in CAN_LIST for chi in CHI_LIST]
CAN_CHI_LIST_NOSPACE = [f"{can}{chi}" for can in CAN_LIST for chi in CHI_LIST]

def get_can_chi_ngay(year, month, day):
    can_list = CAN_LIST
    chi_list = CHI_LIST
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    can = can_list[(jd + 9) % 10]
    chi = chi_list[(jd + 1) % 12]
    return f"{can} {chi}"

def extract_so_hap_chotso(chuoi, can, amduong):
    """Lấy các số đặc biệt cho chốt số dựa trên quy tắc Âm/Dương và chuỗi mệnh"""
    if not chuoi:
        return []
    # Từ chuỗi "5-6,1" lấy ra ['5', '6'] và số chủ '1'
    parts = chuoi.replace(" ", "").split(",")
    cap = parts[0].split("-") if "-" in parts[0] else [parts[0]]
    so_chu = parts[1] if len(parts) > 1 else ""
    # Nếu can là Âm → chọn số chủ, Dương → chọn cả hai số
    result = []
    if amduong == "Âm" and so_chu:
        result = [so_chu]
    else:
        result = cap
    # Trả về các số lô đề 2 số (ghép với nhau và lặp số chủ nếu có)
    lo = set()
    if len(result) == 1:
        lo.add(result[0] + result[0])
    elif len(result) == 2:
        lo.add(result[0] + result[1])
        lo.add(result[1] + result[0])
    if so_chu:
        lo.add(so_chu + so_chu)
    return list(lo), result, so_chu

async def chotso_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    day, month, year = now.day, now.month, now.year
    date_str = now.strftime("%d/%m/%Y")
    can_chi = get_can_chi_ngay(year, month, day)
    can = can_chi.split()[0]
    so = CAN_CHI_DICT.get(can_chi, None)
    caninfo = CAN_INFO.get(can, {})
    amduong = caninfo.get("am_duong", "?")
    # Lấy số hạp cho chốt số
    lo, cap, so_chu = extract_so_hap_chotso(so, can, amduong)
    chams = ", ".join(cap)
    msg = f"Chốt số MB ngày {date_str}\n"
    msg += f"Đầu - đuôi - G1 chạm {chams}"
    if so_chu:
        msg += f" ({so_chu} mạnh)"
    msg += f"\nLô: {', '.join(lo) if lo else 'Không có'}"
    await update.message.reply_text(msg)
    context.user_data["mode"] = None

async def chotso_ngay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        # Hỗ trợ nhiều kiểu ngày: 15-7-2025, 15/7/2025, 15-7, 15/7, Ất Dậu...
        # Nhận ngày
        parts = []
        for sep in ["-", "/", " "]:
            if sep in text:
                parts = [int(x) for x in text.replace("/", sep).replace("-", sep).split(sep) if x.isdigit()]
                break
        if not parts:
            parts = [int(x) for x in text.strip().split() if x.isdigit()]
        if len(parts) == 3:
            d, m, y = parts
        elif len(parts) == 2:
            d, m = parts
            y = datetime.now().year
        else:
            # Có thể nhập can chi
            user_can_chi = text.title().replace(" ", "")
            can_chi = None
            if text.title() in CAN_CHI_LIST:
                can_chi = text.title()
            elif user_can_chi in CAN_CHI_LIST_NOSPACE:
                idx = CAN_CHI_LIST_NOSPACE.index(user_can_chi)
                can_chi = CAN_CHI_LIST[idx]
            else:
                await update.message.reply_text("Sai định dạng ngày! Nhập dd-mm-yyyy, dd-mm, dd/mm/yyyy, dd/mm hoặc tên can chi (VD: Ất Dậu).")
                context.user_data["mode"] = None
                return
            can = can_chi.split()[0]
            so = CAN_CHI_DICT.get(can_chi, None)
            caninfo = CAN_INFO.get(can, {})
            amduong = caninfo.get("am_duong", "?")
            lo, cap, so_chu = extract_so_hap_chotso(so, can, amduong)
            chams = ", ".join(cap)
            msg = f"Chốt số MB ngày {can_chi}\n"
            msg += f"Đầu - đuôi - G1 chạm {chams}"
            if so_chu:
                msg += f" ({so_chu} mạnh)"
            msg += f"\nLô: {', '.join(lo) if lo else 'Không có'}"
            await update.message.reply_text(msg)
            context.user_data["mode"] = None
            return
        # Nếu nhập ngày dương
        can_chi = get_can_chi_ngay(y, m, d)
        date_str = f"{d:02d}/{m:02d}/{y}"
        can = can_chi.split()[0]
        so = CAN_CHI_DICT.get(can_chi, None)
        caninfo = CAN_INFO.get(can, {})
        amduong = caninfo.get("am_duong", "?")
        lo, cap, so_chu = extract_so_hap_chotso(so, can, amduong)
        chams = ", ".join(cap)
        msg = f"Chốt số MB ngày {date_str}\n"
        msg += f"Đầu - đuôi - G1 chạm {chams}"
        if so_chu:
            msg += f" ({so_chu} mạnh)"
        msg += f"\nLô: {', '.join(lo) if lo else 'Không có'}"
        await update.message.reply_text(msg)
    except Exception:
        await update.message.reply_text("Sai định dạng ngày! Nhập dd-mm-yyyy, dd-mm, dd/mm/yyyy, dd/mm hoặc tên can chi (VD: Ất Dậu).")
    context.user_data["mode"] = None

import re
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from can_chi_dict import data as CAN_CHI_DICT
from thien_can import CAN_INFO

CAN_LIST = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
CHI_LIST = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
CAN_CHI_LIST = [f"{can} {chi}" for can in CAN_LIST for chi in CHI_LIST]
CAN_CHI_LIST_NOSPACE = [f"{can}{chi}".lower() for can in CAN_LIST for chi in CHI_LIST]

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

def get_cham_manh(so_str, amduong):
    """Lấy số chạm, số mạnh dựa vào dict (ví dụ: '6,1')"""
    cham = ""
    manh = ""
    if not so_str:
        return [], ""
    if "," in so_str:
        cham, manh = so_str.split(",", 1)
        cham = cham.strip()
        manh = manh.strip()
    else:
        cham = so_str.strip()
        manh = ""
    chams = cham.split("-")
    if amduong == "Âm" and manh:
        return chams, manh
    else:
        return chams, chams[0] if chams else ""

def generate_lo(chams, manh):
    lo = []
    if len(chams) == 1:
        lo.append(chams[0] + chams[0])
    elif len(chams) >= 2:
        lo.append(chams[0] + chams[1])
        lo.append(chams[1] + chams[0])
    if manh:
        lo.append(manh + manh)
    return list(dict.fromkeys(lo)), (manh + manh if manh else None)

async def chotso_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    d, m, y = now.day, now.month, now.year
    can_chi = get_can_chi_ngay(y, m, d)
    date_str = f"{d:02d}/{m:02d}/{y}"

    so_str = CAN_CHI_DICT.get(can_chi, "")
    can = can_chi.split()[0]
    caninfo = CAN_INFO.get(can, {})
    amduong = caninfo.get("am_duong", "?")
    chams, manh = get_cham_manh(so_str, amduong)
    lo_list, lo_manh = generate_lo(chams, manh)

    msg = f"Chốt số ngày {date_str}\n"
    msg += f"Đầu - Đuôi - G1: chạm {', '.join(chams)}"
    if manh:
        msg += f" (mạnh C{manh})"
    msg += f"\nLô: {', '.join(lo_list)}"
    if lo_manh:
        msg += f" mạnh {lo_manh}"
    await update.message.reply_text(msg)
    context.user_data["mode"] = None

async def chotso_ngay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        # Chuẩn hóa cho phép nhập ngày hoặc can chi, không phân biệt hoa thường/cách
        text_lower = re.sub(r"\s+", "", text).lower()
        can_chi = None
        date_str = text
        # Nếu nhập dạng ngày
        parts = re.split(r"[-/ ]", text)
        parts = [int(x) for x in parts if x.isdigit()]
        if len(parts) == 3:
            d, m, y = parts
            can_chi = get_can_chi_ngay(y, m, d)
            date_str = f"{d:02d}/{m:02d}/{y}"
        elif len(parts) == 2:
            d, m = parts
            y = datetime.now().year
            can_chi = get_can_chi_ngay(y, m, d)
            date_str = f"{d:02d}/{m:02d}/{y}"
        else:
            # Thử can chi không phân biệt hoa thường/cách
            for idx, c in enumerate(CAN_CHI_LIST_NOSPACE):
                if c == text_lower:
                    can_chi = CAN_CHI_LIST[idx]
                    date_str = CAN_CHI_LIST[idx]
                    break
            if not can_chi:
                await update.message.reply_text(
                    "Sai định dạng ngày! Nhập dd-mm, dd-mm-yyyy, dd/mm, dd/mm/yyyy hoặc tên can chi (VD: Ất Dậu)."
                )
                context.user_data["mode"] = None
                return

        so_str = CAN_CHI_DICT.get(can_chi, "")
        can = can_chi.split()[0]
        caninfo = CAN_INFO.get(can, {})
        amduong = caninfo.get("am_duong", "?")
        chams, manh = get_cham_manh(so_str, amduong)
        lo_list, lo_manh = generate_lo(chams, manh)

        msg = f"Chốt số ngày {date_str}\n"
        msg += f"Đầu - Đuôi - G1: chạm {', '.join(chams)}"
        if manh:
            msg += f" (mạnh C{manh})"
        msg += f"\nLô: {', '.join(lo_list)}"
        if lo_manh:
            msg += f" mạnh {lo_manh}"
        await update.message.reply_text(msg)
    except Exception:
        await update.message.reply_text(
            "Sai định dạng ngày! Nhập dd-mm, dd-mm-yyyy, dd/mm, dd/mm/yyyy hoặc tên can chi (VD: Ất Dậu)."
        )
    context.user_data["mode"] = None

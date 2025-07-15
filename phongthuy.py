from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from can_chi_dict import data as CAN_CHI_DICT
from thien_can import CAN_INFO

CAN_LIST = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
CHI_LIST = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']

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

def extract_so_hap(chuoi):
    so_hap = []
    if not chuoi:
        return so_hap
    parts = chuoi.replace(" ", "").split(",")
    if parts and "-" in parts[0]:
        so1, so2 = parts[0].split("-")
        so_hap.extend([f"{so1}{so2}", f"{so2}{so1}"])
    if len(parts) > 1 and parts[1]:
        so_hap.append(parts[1]*2)
        so1, so2 = parts[0].split("-")
        so_hap.append(f"{so1}{parts[1]}")
        so_hap.append(f"{so2}{parts[1]}")
        so_hap.append(f"{parts[1]}{so1}")
        so_hap.append(f"{parts[1]}{so2}")
    return list(dict.fromkeys(so_hap))

async def phongthuy_homnay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    can_chi = get_can_chi_ngay(now.year, now.month, now.day)
    so = CAN_CHI_DICT.get(can_chi, None)
    can = can_chi.split()[0]
    caninfo = CAN_INFO.get(can, {})
    amduong = caninfo.get("am_duong", "?")
    nguhanh = caninfo.get("ngu_hanh", "?")
    so_hap = extract_so_hap(so) if so else []
    so_main = so.split(",")[1] if so and "," in so else ""
    so_hap_str = ", ".join(so_hap)
    msg = f"**Phong thủy số ngày hôm nay:**\n"
    msg += f"Ngày {can_chi}, {amduong} {nguhanh}"
    if so:
        msg += f", hạp {so}."
    else:
        msg += "."
    if so_main:
        msg += f" (Chủ yếu {so_main})\n"
    else:
        msg += "\n"
    if so_hap_str:
        msg += f"Số hạp ngày: {so_hap_str}."
    else:
        msg += "Không có dữ liệu số hạp cho ngày này."
    await update.callback_query.edit_message_text(msg, parse_mode="Markdown")

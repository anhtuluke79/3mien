from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
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

def extract_so_hap(chuoi):
    """Từ chuỗi '5-6,1' -> trả về list ['15','51','16','61','11']"""
    so_hap = []
    # Chuỗi có thể dạng '5-6,1' hoặc chỉ '5-6'
    parts = chuoi.replace(" ", "").split(",")
    # Phần đầu: các cặp (vd: 5-6)
    if parts and "-" in parts[0]:
        so1, so2 = parts[0].split("-")
        so_hap.extend([
            f"{so1}{so2}", f"{so2}{so1}"
        ])
    # Phần sau: số chủ
    if len(parts) > 1 and parts[1]:
        so_hap.append(parts[1]*2)  # VD: "1" -> "11"
        # Gộp thành "1" với mỗi số trong phần đầu
        so1, so2 = parts[0].split("-")
        so_hap.append(f"{so1}{parts[1]}")
        so_hap.append(f"{so2}{parts[1]}")
        so_hap.append(f"{parts[1]}{so1}")
        so_hap.append(f"{parts[1]}{so2}")
    # Loại bỏ trùng
    return list(dict.fromkeys(so_hap))

def tra_cuu_phong_thuy(can_chi):
    so = CAN_CHI_DICT.get(can_chi, None)
    if not so:
        return None
    so_main = so.split(",")[1] if "," in so else ""
    can = can_chi.split()[0]
    caninfo = CAN_INFO.get(can, {})
    amduong = caninfo.get("am_duong", "?")
    nguhanh = caninfo.get("ngu_hanh", "?")
    # Lấy danh sách số hạp
    so_hap = extract_so_hap(so)
    so_hap_str = ", ".join(so_hap)
    # Chuẩn thông điệp
    msg = (
        f"**Phong thủy số ngày hôm nay:**\n"
        f"Ngày {can_chi}, {amduong} {nguhanh}, hạp {so}. "
    )
    if so_main:
        msg += f"(Chủ yếu {so_main})\n"
    else:
        msg += "\n"
    msg += f"Số hạp ngày: {so_hap_str}."
    return msg

async def phongthuy_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")
    try:
        # --- PHONG THỦY HÔM NAY ---
        if mode == "phongthuy_today":
            now = datetime.now()
            can_chi = get_can_chi_ngay(now.year, now.month, now.day)
        # --- PHONG THỦY THEO NGÀY hoặc TRA CAN CHI ---
        elif mode == "phongthuy":
            # Nhập ngày dương lịch
            if '-' in text and len(text.split('-')) in (2, 3):
                parts = [int(x) for x in text.split('-')]
                if len(parts) == 3:
                    y, m, d = parts
                elif len(parts) == 2:
                    now = datetime.now()
                    d, m = parts
                    y = now.year
                else:
                    raise ValueError
                can_chi = get_can_chi_ngay(y, m, d)
            # Nhập can chi dạng chữ
            else:
                user_can_chi = text.title().replace(" ", "")
                can_chi = None
                if text.title() in CAN_CHI_LIST:
                    can_chi = text.title()
                elif user_can_chi in CAN_CHI_LIST_NOSPACE:
                    idx = CAN_CHI_LIST_NOSPACE.index(user_can_chi)
                    can_chi = CAN_CHI_LIST[idx]
                if not can_chi:
                    raise ValueError
        else:
            await update.message.reply_text("Vui lòng chọn lại chức năng từ menu phong thủy.")
            context.user_data["mode"] = None
            return

        # Tra cứu và trả kết quả
        result = tra_cuu_phong_thuy(can_chi)
        if result:
            await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"Không tìm thấy dữ liệu phong thủy cho ngày {can_chi}.")
    except Exception:
        await update.message.reply_text("❗️ Lỗi định dạng! Hãy nhập ngày YYYY-MM-DD, DD-MM hoặc tên can chi.")

    context.user_data["mode"] = None

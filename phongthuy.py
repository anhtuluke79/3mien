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

async def phongthuy_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")
    try:
        # -- Chỉ xử lý nếu user đang ở mode "phongthuy"
        if mode != "phongthuy":
            return

        # Nhận các kiểu phân cách: 15-7-2025, 15/7/2025, 15-7, 15/7
        for sep in ["-", "/"]:
            if sep in text:
                parts = [int(x) for x in text.split(sep) if x.isdigit()]
                break
        else:
            # Nếu không có -, / thì thử split theo space
            parts = [int(x) for x in text.split() if x.isdigit()]
        
        # Xử lý parts: parts = [day, month, year] hoặc [day, month]
        if len(parts) == 3:
            d, m, y = parts
        elif len(parts) == 2:
            d, m = parts
            y = datetime.now().year
        else:
            await update.message.reply_text("Sai định dạng ngày! Nhập kiểu dd-mm-yyyy, dd-mm hoặc dd/mm/yyyy, dd/mm.")
            context.user_data["mode"] = None
            return
        
        can_chi = get_can_chi_ngay(y, m, d)
        so = CAN_CHI_DICT.get(can_chi, None)
        can = can_chi.split()[0]
        caninfo = CAN_INFO.get(can, {})
        amduong = caninfo.get("am_duong", "?")
        nguhanh = caninfo.get("ngu_hanh", "?")
        so_hap = extract_so_hap(so) if so else []
        so_main = so.split(",")[1] if so and "," in so else ""
        so_hap_str = ", ".join(so_hap)
        msg = f"**Phong thủy số ngày tra cứu:**\n"
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
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("Lỗi định dạng ngày! Nhập kiểu dd-mm-yyyy, dd-mm hoặc dd/mm/yyyy, dd/mm.")

    # Reset mode sau khi trả lời để tránh kẹt state
    context.user_data["mode"] = None

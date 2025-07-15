from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime

# --- Dữ liệu mẫu Can Chi và chuỗi số ---
from can_chi_dict import data as CAN_CHI_DICT  # dict: "Giáp Tý": "4-9,4"
from thien_can import CAN_INFO  # dict: "Giáp": {...}

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

def phong_thuy_info(can_chi):
    # Lấy số mệnh đặc biệt từ dict
    so_menh = CAN_CHI_DICT.get(can_chi, None)
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    # Tạo đoạn giải thích phong thủy tổng hợp
    explain = []
    explain.append(f"🔮 **Can Chi ngày:** `{can_chi}`")
    if can_info:
        explain.append(f"• Âm/Dương: **{can_info.get('am_duong','?')}**")
        explain.append(f"• Ngũ hành: **{can_info.get('ngu_hanh','?')}**")
        explain.append(f"• Phương vị: **{can_info.get('phuong','?')}**")
    if so_menh:
        explain.append(f"• Chuỗi số mệnh: `{so_menh}`")
    explain.append("\n*Hãy dùng ngày này để tham khảo các công việc, xuất hành, cầu tài, chọn số đẹp...*")
    return "\n".join(explain)

async def phongthuy_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")
    try:
        # --- PHONG THỦY HÔM NAY ---
        if mode == "phongthuy_today":
            now = datetime.now()
            can_chi = get_can_chi_ngay(now.year, now.month, now.day)
            info = phong_thuy_info(can_chi)
            await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
            context.user_data["mode"] = None
            return

        # --- PHONG THỦY THEO NGÀY hoặc TRA CAN CHI ---
        if mode == "phongthuy":
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
                info = phong_thuy_info(can_chi)
                await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
                context.user_data["mode"] = None
                return
            # Nhập trực tiếp Can Chi
            user_can_chi = text.title().replace(" ", "")
            can_chi_match = None
            if text.title() in CAN_CHI_LIST:
                can_chi_match = text.title()
            elif user_can_chi in CAN_CHI_LIST_NOSPACE:
                idx = CAN_CHI_LIST_NOSPACE.index(user_can_chi)
                can_chi_match = CAN_CHI_LIST[idx]
            if can_chi_match:
                info = phong_thuy_info(can_chi_match)
                await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
                context.user_data["mode"] = None
                return
            # Không hợp lệ
            await update.message.reply_text(
                "❗️ Vui lòng nhập ngày dạng YYYY-MM-DD, DD-MM hoặc tên can chi hợp lệ (VD: Giáp Tý, Đinh Hợi)."
            )
            context.user_data["mode"] = None
            return

        await update.message.reply_text("❗️ Vui lòng chọn lại chức năng từ menu phong thủy.")
    except Exception:
        await update.message.reply_text("❗️ Lỗi định dạng! Hãy nhập ngày YYYY-MM-DD, DD-MM hoặc tên can chi.")
        context.user_data["mode"] = None

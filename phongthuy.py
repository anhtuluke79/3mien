from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime

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
    return f"Can Chi ngày: {can_chi}\n(Nhập ngày dạng YYYY-MM-DD, DD-MM hoặc trực tiếp Can Chi, ví dụ: Giáp Tý, Đinh Hợi)"

async def phongthuy_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")
    try:
        # --- Tra cứu phong thủy hôm nay ---
        if mode == "phongthuy_today":
            now = datetime.now()
            can_chi = get_can_chi_ngay(now.year, now.month, now.day)
            info = phong_thuy_info(can_chi)
            await update.message.reply_text(f"🔮 {info}", parse_mode=ParseMode.MARKDOWN)
            context.user_data["mode"] = None
            return

        # --- Tra cứu theo ngày nhập vào ---
        if mode == "phongthuy":
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
                await update.message.reply_text(f"🔮 {info}", parse_mode=ParseMode.MARKDOWN)
                context.user_data["mode"] = None
                return

            # --- Tra cứu bằng Can Chi ---
            user_can_chi = text.title().replace(" ", "")
            can_chi_match = None
            if text.title() in CAN_CHI_LIST:
                can_chi_match = text.title()
            elif user_can_chi in CAN_CHI_LIST_NOSPACE:
                idx = CAN_CHI_LIST_NOSPACE.index(user_can_chi)
                can_chi_match = CAN_CHI_LIST[idx]
            if can_chi_match:
                info = phong_thuy_info(can_chi_match)
                await update.message.reply_text(f"🔮 {info}", parse_mode=ParseMode.MARKDOWN)
                context.user_data["mode"] = None
                return

            # Nếu không khớp, báo lại cho user
            await update.message.reply_text(
                "❗️ Vui lòng nhập ngày dạng YYYY-MM-DD, DD-MM hoặc tên can chi hợp lệ (VD: Giáp Tý, Đinh Hợi)."
            )
            context.user_data["mode"] = None
            return

        # Nếu đến đây mà không có mode phù hợp
        await update.message.reply_text("❗️ Vui lòng chọn chức năng từ menu phong thủy.")
    except Exception:
        await update.message.reply_text("❗️ Lỗi định dạng! Hãy nhập kiểu YYYY-MM-DD, DD-MM hoặc tên can chi.")
        context.user_data["mode"] = None

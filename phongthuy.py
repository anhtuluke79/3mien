from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime

def get_can_chi_ngay(year, month, day):
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
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
    return f"Can Chi ngày: {can_chi}\n(Nhập ngày dạng YYYY-MM-DD để tra can chi!)"

async def phongthuy_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
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
        else:
            await update.message.reply_text("❗️ Vui lòng nhập ngày dạng YYYY-MM-DD hoặc DD-MM để tra cứu can chi/phong thủy!")
    except Exception:
        await update.message.reply_text("❗️ Lỗi định dạng ngày! Hãy nhập kiểu YYYY-MM-DD hoặc DD-MM.")

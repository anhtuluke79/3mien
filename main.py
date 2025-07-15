import os
import logging
from datetime import datetime
from itertools import combinations, permutations

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)

# -- Data phong thủy: tạo file can_chi_dict.py, thien_can.py như hướng dẫn --
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# -- Config bot --
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("XSMB-BOT")

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

# -- Tiện ích xử lý số và phong thủy --
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

def get_can_chi_ngay(year, month, day):
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    can = can_list[(jd + 9) % 10]
    chi = chi_list[(jd + 1) % 12]
    return f"{can} {chi}"

def sinh_so_hap_cho_ngay(can_chi_str):
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code: return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j: ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can, "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"), "so_menh": so_menh,
        "so_hap_list": so_ghep, "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else: so_hap_can, so_menh = "?", "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 *Phong thủy NGÀY HIỆN TẠI*: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 *Phong thủy số ngũ hành cho ngày* {can_chi}:"
    text = (
        f"{main_line}\n- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n- Số hạp ngày: {so_hap_ngay}"
    )
    return text

def chot_so_format(can_chi, sohap_info, today_str):
    if not sohap_info or not sohap_info.get("so_hap_list"):
        return "Không đủ dữ liệu phong thủy để chốt số hôm nay!"
    d = [sohap_info['so_menh']] + sohap_info['so_hap_list']
    chams = ','.join(d)
    dan_de = []
    for x in d:
        for y in d:
            dan_de.append(x + y)
    dan_de = sorted(set(dan_de))
    lo = []
    for x in d:
        for y in d:
            if x != y: lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n*Chốt số hôm nay {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text
# ===== 2. MENU, CALLBACK, UI/UX, PHÂN NHÁNH =====

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [
            InlineKeyboardButton("🤖 Dự đoán AI", callback_data="ml_predict"),
            InlineKeyboardButton("🔢 Ghép xiên", callback_data="menu_ghepxien"),
        ],
        [
            InlineKeyboardButton("🎲 Ghép càng/Đảo số", callback_data="menu_ghepcang"),
            InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso"),
            InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho"),
        ],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    await (update.message or update.callback_query.message).reply_text(
        "🌟 *Menu Chính* - Chọn chức năng:\n\n"
        "• Dự đoán AI xổ số\n"
        "• Ghép xiên - càng - đảo số\n"
        "• Tra cứu phong thủy, chốt số may mắn\n"
        "• Hỗ trợ nhiều chế độ tiện ích",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    # ========== DỰ ĐOÁN AI ==========
    if data == "ml_predict":
        await query.edit_message_text(
            "🤖 *Dự đoán AI (DEMO)*\nChức năng này sẽ nâng cấp sau!", parse_mode=ParseMode.MARKDOWN)
        await menu(update, context)
        return
    # ========== GHÉP XIÊN ==========
    if data == "menu_ghepxien":
        await query.edit_message_text(
            "🔢 *GHÉP XIÊN*\n1️⃣ Nhập dãy số (cách nhau bởi dấu cách hoặc phẩy).\n2️⃣ Sau đó nhập độ dài xiên (2, 3 hoặc 4).",
            parse_mode=ParseMode.MARKDOWN)
        context.user_data.clear()
        context.user_data['wait_for_xien_length'] = True
        return
    # ========== GHÉP CÀNG/ĐẢO SỐ ==========
    if data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Ghép càng 3D", callback_data="ghep_cang3d"),
             InlineKeyboardButton("Ghép càng 4D", callback_data="ghep_cang4d")],
            [InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Về menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🎲 Chọn chế độ:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == "ghep_cang3d":
        await query.edit_message_text("Nhập dãy số 2 chữ số (cách nhau bởi dấu cách hoặc phẩy):")
        context.user_data.clear()
        context.user_data['wait_for_cang3d_numbers'] = True
        return
    if data == "ghep_cang4d":
        await query.edit_message_text("Nhập dãy số 3 chữ số (cách nhau bởi dấu cách hoặc phẩy):")
        context.user_data.clear()
        context.user_data['wait_for_cang4d_numbers'] = True
        return
    if data == "daoso":
        await query.edit_message_text("Nhập số muốn đảo hoán vị (2-6 chữ số):")
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        return
    # ========== PHONG THỦY ==========
    if data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("Ngày dương", callback_data="phongthuy_ngay_duong"),
             InlineKeyboardButton("Can chi", callback_data="phongthuy_ngay_canchi")],
            [InlineKeyboardButton("⬅️ Về menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🔮 Chọn cách tra cứu phong thủy:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == "phongthuy_ngay_duong":
        await query.edit_message_text("Nhập ngày dương (YYYY-MM-DD):")
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_duong'] = True
        return
    if data == "phongthuy_ngay_canchi":
        await query.edit_message_text("Nhập can chi ngày (VD: Giáp Tý):")
        context.user_data.clear()
        context.user_data['wait_phongthuy_ngay_canchi'] = True
        return
    # ========== CHỐT SỐ ==========
    if data == "menu_chotso":
        await query.edit_message_text("Nhập ngày dương (YYYY-MM-DD hoặc DD-MM):")
        context.user_data.clear()
        context.user_data['wait_chot_so_ngay'] = True
        return
    # ========== ỦNG HỘ ==========
    if data == "ungho":
        await query.edit_message_text("💗 *Cảm ơn bạn đã ủng hộ bot!*", parse_mode=ParseMode.MARKDOWN)
        return
    # ========== ADMIN ==========
    if data == "admin_menu":
        await query.edit_message_text("🔒 Menu quản trị sẽ phát triển thêm.", parse_mode=ParseMode.MARKDOWN)
        return
    # ========== MAIN MENU ==========
    if data == "main_menu":
        await menu(update, context)
        return
    await query.edit_message_text("Chức năng chưa phát triển hoặc không hợp lệ.\nGõ /menu để về menu chính.")
# ===== 3. TEXT HANDLERS, MAIN, HELP, ERROR =====

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data

    # 1. Ghép xiên - Nhập độ dài xiên
    if state.get('wait_for_xien_length'):
        try:
            do_dai = int(update.message.text.strip())
            if do_dai not in (2, 3, 4): raise ValueError
            context.user_data.clear()
            context.user_data['wait_for_xien_input'] = do_dai
            await update.message.reply_text(f"Nhập các số (cách nhau bởi dấu cách hoặc phẩy) để ghép xiên {do_dai} số:")
        except:
            await update.message.reply_text("Vui lòng nhập độ dài xiên hợp lệ (2, 3 hoặc 4)!")
        return

    # 2. Ghép xiên - Nhập dãy số
    if isinstance(state.get('wait_for_xien_input'), int):
        numbers = split_numbers(update.message.text)
        do_dai = state['wait_for_xien_input']
        bo_xien = ghep_xien(numbers, do_dai)
        if not bo_xien:
            await update.message.reply_text("Không ghép được xiên.")
        else:
            if len(bo_xien) > 20:
                result = '\n'.join([', '.join(bo_xien[i:i+10]) for i in range(0, len(bo_xien), 10)])
            else:
                result = ', '.join(bo_xien)
            await update.message.reply_text(f"{len(bo_xien)} bộ xiên:\n{result}")
        context.user_data.clear()
        await menu(update, context)
        return

    # 3. Ghép càng 3D
    if state.get('wait_for_cang3d_numbers'):
        arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 2]
        if not arr:
            await update.message.reply_text("Vui lòng nhập các số 2 chữ số (VD: 23 32 28 ...)")
            return
        context.user_data.clear()
        context.user_data['cang3d_numbers'] = arr
        context.user_data['wait_for_cang3d_cangs'] = True
        await update.message.reply_text("Nhập các càng (1 chữ số, cách nhau dấu cách hoặc phẩy, VD: 1 2 3):")
        return
    if state.get('wait_for_cang3d_cangs'):
        cang_list = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 1]
        numbers = context.user_data.get('cang3d_numbers', [])
        if not cang_list or not numbers:
            await update.message.reply_text("Vui lòng nhập các càng (1 chữ số, VD: 1 2 3):")
            return
        result = [c + n for c in cang_list for n in numbers]
        await update.message.reply_text(f"Kết quả ghép càng 3D ({len(result)} số):\n" + ', '.join(result))
        context.user_data.clear()
        await menu(update, context)
        return

    # 4. Ghép càng 4D
    if state.get('wait_for_cang4d_numbers'):
        arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 3]
        if not arr:
            await update.message.reply_text("Vui lòng nhập các số 3 chữ số (VD: 123 234 ...)")
            return
        context.user_data.clear()
        context.user_data['cang4d_numbers'] = arr
        context.user_data['wait_for_cang4d_cangs'] = True
        await update.message.reply_text("Nhập các càng (1 chữ số, VD: 1 2 3):")
        return
    if state.get('wait_for_cang4d_cangs'):
        cang_list = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 1]
        numbers = context.user_data.get('cang4d_numbers', [])
        if not cang_list or not numbers:
            await update.message.reply_text("Vui lòng nhập các càng (1 chữ số, VD: 1 2 3):")
            return
        result = [c + n for c in cang_list for n in numbers]
        await update.message.reply_text(f"Kết quả ghép càng 4D ({len(result)} số):\n" + ', '.join(result))
        context.user_data.clear()
        await menu(update, context)
        return

    # 5. Đảo số
    if state.get('wait_for_daoso'):
        s = update.message.text.strip()
        arr = split_numbers(s)
        s_concat = ''.join(arr) if arr else s.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text("Nhập số từ 2 đến 6 chữ số (VD: 1234, 56789).")
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}")
        context.user_data.clear()
        await menu(update, context)
        return

    # 6. Chốt số theo ngày dương (YYYY-MM-DD hoặc DD-MM)
    if state.get('wait_chot_so_ngay'):
        try:
            ngay = update.message.text.strip()
            parts = [int(x) for x in ngay.replace('/', '-').split('-')]
            if len(parts) == 3:
                y, m, d = parts
            elif len(parts) == 2:
                now = datetime.now()
                d, m = parts
                y = now.year
            else:
                raise ValueError
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            today_str = f"{d:02d}/{m:02d}/{y}"
            text = chot_so_format(can_chi, sohap_info, today_str)
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except:
            await update.message.reply_text("❗️ Nhập ngày không hợp lệ! Đúng định dạng: YYYY-MM-DD hoặc DD-MM.")
        context.user_data.clear()
        await menu(update, context)
        return

    # 7. Phong thủy theo ngày dương
    if state.get('wait_phongthuy_ngay_duong'):
        try:
            y, m, d = map(int, update.message.text.strip().split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if sohap_info is None:
                await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp cho ngày này!")
            else:
                text = phong_thuy_format(can_chi, sohap_info, is_today=True, today_str=f"{d:02d}/{m:02d}/{y}")
                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text("❗️ Nhập ngày không hợp lệ! Đúng định dạng YYYY-MM-DD.")
        context.user_data.clear()
        await menu(update, context)
        return

    # 8. Phong thủy theo can chi
    if state.get('wait_phongthuy_ngay_canchi'):
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if sohap_info is None:
            await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp với tên bạn nhập! VD: Giáp Tý.")
        else:
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        context.user_data.clear()
        await menu(update, context)
        return

    # --- Nếu không thuộc trạng thái nào, về menu ---
    await menu(update, context)

# --- /help ---
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Bot Dự đoán & Phong thủy XSMB*\n\n"
        "Các lệnh hỗ trợ:\n"
        "• /start hoặc /menu - Mở menu chính\n"
        "• /help - Xem hướng dẫn, chức năng\n\n"
        "*Chức năng nổi bật:*\n"
        "• Dự đoán AI xổ số miền Bắc (demo)\n"
        "• Ghép xiên, càng, đảo số, thống kê tiện ích\n"
        "• Tra cứu phong thủy, chốt số may mắn\n"
        "• Giao diện thân thiện, dễ dùng, hỗ trợ mobile\n"
        "• Được phát triển bởi @tutruong19790519"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# --- Xử lý lỗi toàn cục ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚨 Exception:\n{context.error}"
            )
        except Exception:
            pass

# --- MAIN ENTRY ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.add_error_handler(error_handler)
    logger.info("🤖 BOT XSMB đã chạy thành công!")
    app.run_polling()

if __name__ == "__main__":
    main()

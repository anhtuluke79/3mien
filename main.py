import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)
from itertools import product, combinations, permutations
import csv
from datetime import datetime, timedelta
import re
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

# ============= CONFIG ============
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= TIỆN ÍCH ============
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0:
        return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

# ==== SỬA CODE: HÀM CAN CHI NGÀY DƯƠNG CHUẨN HƠN ====
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
    if not code:
        return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j:
                ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can,
        "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"),
        "so_menh": so_menh,
        "so_hap_list": so_ghep,
        "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    so_hap_can = sohap_info['so_hap_list'][0] if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) > 0 else "?"
    so_menh = sohap_info['so_menh'] if sohap_info else "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"

    if is_today and today_str:
        tieu_de = f"*Ngày hiện tại*"
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        tieu_de = f"*ngày {can_chi}*"
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"

    text = (
        f"{tieu_de}\n"
        f"{main_line}\n"
        f"- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n"
        f"- Số hạp ngày: {so_hap_ngay}"
    )
    return text

# ========== CRAWL XỔ SỐ KẾT QUẢ NHIỀU NGÀY ==========
def crawl_xsketqua_mien_multi(region: str, days: int = 30, progress_callback=None):
    region = region.lower()
    XSKQ_CONFIG = {
        "bac": {"csv": "xsmb.csv"},
        "trung": {"csv": "xsmt.csv"},
        "nam": {"csv": "xsmn.csv"},
    }
    if region not in XSKQ_CONFIG:
        raise ValueError("Miền không hợp lệ. Chọn: 'bac', 'trung', 'nam'.")
    csv_file = XSKQ_CONFIG[region]['csv']
    rows = []
    if os.path.exists(csv_file):
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.reader(f))
    dates_exist = set(row[0] for row in rows)
    count = 0
    today = datetime.now()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for i in range(days * 2):
        date = today - timedelta(days=i)
        date_str = date.strftime("%d-%m-%Y")
        if region == "bac":
            url = f"https://xosoketqua.com/xsmb-{date.strftime('%d-%m-%Y')}.html"
        elif region == "trung":
            url = f"https://xosoketqua.com/xsmt-{date.strftime('%d-%m-%Y')}.html"
        else:
            url = f"https://xosoketqua.com/xsmn-{date.strftime('%d-%m-%Y')}.html"
        if date_str.replace("-", "/") in dates_exist or date_str in dates_exist:
            continue
        try:
            res = requests.get(url, timeout=10, headers=headers)
            print(f"DEBUG: {url} => status {res.status_code}")
            if res.status_code != 200:
                print(f"Failed ({res.status_code}): {url}")
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.select_one("table.tblKQXS")
            if not table:
                print("Không tìm thấy bảng kết quả!")
                continue
            results = []
            for row in table.select("tr"):
                tds = row.find_all("td", class_="bcls")
                if not tds:
                    continue
                for td in tds:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        results.append(txt)
                    elif " " in txt:
                        results.extend([x for x in txt.split() if x.isdigit()])
            if not results:
                continue
            with open(csv_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([date_str] + results)
            dates_exist.add(date_str)
            count += 1
            if progress_callback and (count % 2 == 0 or count == days):
                progress_callback(count, days)
            if count >= days:
                break
        except Exception as e:
            print(f"Lỗi crawl {region} {date_str}: {e}")
            continue
    return count

# ========== UPDATE DATA MIỀN (chỉ admin, báo tiến trình) ==========
async def capnhat_xsm_kq_handler_query(query, region: str, region_label: str):
    try:
        import asyncio
        msg = await query.edit_message_text(f"⏳ Đang cập nhật 0/30 ngày {region_label} từ xosoketqua.com...")
        progress = {"last_count": 0}
        def progress_callback(count, total):
            if count != progress["last_count"]:
                try:
                    asyncio.run_coroutine_threadsafe(
                        msg.edit_text(f"⏳ Đang cập nhật {count}/{total} ngày {region_label}..."),
                        asyncio.get_event_loop()
                    )
                    progress["last_count"] = count
                except Exception:
                    pass
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, crawl_xsketqua_mien_multi, region, 30, progress_callback)
        await msg.edit_text(f"✅ Đã cập nhật {result} ngày {region_label}!")
    except Exception as e:
        await query.edit_message_text(f"❌ Lỗi crawl {region_label}: {e}")

# ========== MENU & CALLBACK ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("💗 Đóng góp", callback_data="donggop")],
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("🛠️ Update MB", callback_data="capnhat_xsmb_kq"),
            InlineKeyboardButton("🛠️ Update MT", callback_data="capnhat_xsmt_kq"),
            InlineKeyboardButton("🛠️ Update MN", callback_data="capnhat_xsmn_kq"),
        ])
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ===== Menu phụ Ghép xiên
    if query.data == "menu_ghepxien":
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="ghepxien_2"),
             InlineKeyboardButton("Xiên 3", callback_data="ghepxien_3"),
             InlineKeyboardButton("Xiên 4", callback_data="ghepxien_4")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ===== Menu phụ Ghép càng/đảo số
    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("Càng 3D", callback_data="ghepcang_3d"),
             InlineKeyboardButton("Càng 4D", callback_data="ghepcang_4d"),
             InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Chọn loại càng hoặc đảo số:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ===== Quay lại menu chính
    if query.data == "main_menu":
        await menu(update, context)
        return

    # ====== Ghép xiên/càng/đảo số
    if query.data == "ghepxien_2":
        context.user_data['wait_for_xien_input'] = 2
        await query.edit_message_text("Nhập dãy số để ghép xiên 2 (cách nhau dấu cách hoặc phẩy):")
    elif query.data == "ghepxien_3":
        context.user_data['wait_for_xien_input'] = 3
        await query.edit_message_text("Nhập dãy số để ghép xiên 3 (cách nhau dấu cách hoặc phẩy):")
    elif query.data == "ghepxien_4":
        context.user_data['wait_for_xien_input'] = 4
        await query.edit_message_text("Nhập dãy số để ghép xiên 4 (cách nhau dấu cách hoặc phẩy):")
    elif query.data == "ghepcang_3d":
        context.user_data['wait_for_cang_input'] = 3
        await query.edit_message_text("Nhập dãy số để ghép càng 3D (cách nhau dấu cách hoặc phẩy):")
    elif query.data == "ghepcang_4d":
        context.user_data['wait_for_cang_input'] = 4
        await query.edit_message_text("Nhập dãy số để ghép càng 4D (cách nhau dấu cách hoặc phẩy):")
    elif query.data == "daoso":
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text("Nhập một số hoặc dãy số (VD: 123 hoặc 1234):")

    # ===== Cập nhật, Phong thủy, Đóng góp
    elif query.data == "capnhat_xsmb_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "bac", "Miền Bắc")
    elif query.data == "capnhat_xsmt_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "trung", "Miền Trung")
    elif query.data == "capnhat_xsmn_kq":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        await capnhat_xsm_kq_handler_query(query, "nam", "Miền Nam")
    elif query.data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("Theo ngày dương (YYYY-MM-DD)", callback_data="phongthuy_ngay_duong")],
            [InlineKeyboardButton("Theo can chi (VD: Giáp Tý)", callback_data="phongthuy_ngay_canchi")],
            [InlineKeyboardButton("Ngày hiện tại", callback_data="phongthuy_ngay_today")],
        ]
        await query.edit_message_text("🔮 Bạn muốn tra phong thủy theo kiểu nào?", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "phongthuy_ngay_duong":
        await query.edit_message_text("📅 Nhập ngày dương lịch (YYYY-MM-DD):")
        context.user_data['wait_phongthuy_ngay_duong'] = True
    elif query.data == "phongthuy_ngay_canchi":
        await query.edit_message_text("📜 Nhập can chi (ví dụ: Giáp Tý):")
        context.user_data['wait_phongthuy_ngay_canchi'] = True
    elif query.data == "phongthuy_ngay_today":
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        can_chi = get_can_chi_ngay(y, m, d)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        today_str = f"{d:02d}/{m:02d}/{y}"
        text = phong_thuy_format(can_chi, sohap_info, is_today=True, today_str=today_str)
        await query.edit_message_text(text, parse_mode="Markdown")
    elif query.data == "donggop":
        keyboard = [
            [InlineKeyboardButton("Gửi góp ý", callback_data="donggop_gui")],
            [InlineKeyboardButton("Danh dự", callback_data="donggop_danhdu")]
        ]
        info = (
            "💗 *Cảm ơn bạn đã quan tâm và ủng hộ bot!*\n\n"
            "Bạn có thể gửi góp ý, ý tưởng và đóng góp 100.000/tháng để bot duy trì phát triển lâu dài.\n"
            "👉 Góp ý: Chọn 'Gửi góp ý' bên dưới hoặc gửi trực tiếp qua Telegram.\n"
            "👉 Ủng hộ: Vietcombank: 0071003914986 (Trương Anh Tú)\n\n"
            "Hoặc xem 'Danh dự' để xem bảng tri ân những người đã gửi góp ý/ủng hộ. 🙏"
        )
        await query.edit_message_text(info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif query.data == "donggop_gui":
        await query.edit_message_text(
            "🙏 Vui lòng nhập góp ý, phản hồi hoặc lời nhắn của bạn (mọi góp ý đều được ghi nhận và tri ân công khai)."
        )
        context.user_data['wait_for_donggop'] = True
    elif query.data == "donggop_danhdu":
        log_file = "donggop_log.txt"
        names = set()
        if os.path.exists(log_file):
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 3:
                        name = parts[1].strip()
                        names.add(name)
        if not names:
            msg = "Chưa có ai gửi góp ý/đóng góp. Hãy là người đầu tiên nhé! 💗"
        else:
            msg = "🏆 *Bảng danh dự những người đã gửi góp ý/ủng hộ:*\n"
            msg += "\n".join([f"❤️ {name}" for name in sorted(names)])
        await query.edit_message_text(msg, parse_mode="Markdown")

# ========== ALL TEXT HANDLER ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # PATCH: Chỉ trả lời group khi có mention @Xs3mbot hoặc lệnh /
    if update.message.chat.type in ["group", "supergroup"]:
        bot_username = "@xs3mbot"
        text = update.message.text.lower()
        if not (text.startswith("/") or bot_username in text):
            return

    # Đóng góp/góp ý
    if context.user_data.get('wait_for_donggop'):
        user = update.message.from_user
        username = user.username or user.full_name or str(user.id)
        text = update.message.text.strip()
        with open("donggop_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {username} | {user.id} | {text}\n")
        await update.message.reply_text(
            "💗 Cảm ơn bạn đã gửi góp ý/ủng hộ! Tất cả phản hồi đều được trân trọng ghi nhận.\n"
            "Bạn có thể tiếp tục sử dụng bot hoặc gửi góp ý thêm bất cứ lúc nào."
        )
        context.user_data['wait_for_donggop'] = False
        await menu(update, context)
        return

    # Ghép xiên N
    if isinstance(context.user_data.get('wait_for_xien_input'), int):
        text_msg = update.message.text.strip()
        numbers = split_numbers(text_msg)
        do_dai = context.user_data.get('wait_for_xien_input')
        bo_xien = ghep_xien(numbers, do_dai)
        if not bo_xien:
            await update.message.reply_text("Không ghép được xiên.")
        else:
            if len(bo_xien) > 20:
                result = '\n'.join([', '.join(bo_xien[i:i+10]) for i in range(0, len(bo_xien), 10)])
            else:
                result = ', '.join(bo_xien)
            await update.message.reply_text(f"{len(bo_xien)} bộ xiên:\n{result}")
        context.user_data['wait_for_xien_input'] = False
        await menu(update, context)
        return

    # Ghép càng N
    if isinstance(context.user_data.get('wait_for_cang_input'), int):
        text_msg = update.message.text.strip()
        numbers = split_numbers(text_msg)
        so_cang = context.user_data.get('wait_for_cang_input')
        bo_so = ghep_cang(numbers, so_cang)
        if not bo_so:
            await update.message.reply_text("Không ghép được càng.")
        else:
            if len(bo_so) > 20:
                result = '\n'.join([', '.join(bo_so[i:i+10]) for i in range(0, len(bo_so), 10)])
            else:
                result = ', '.join(bo_so)
            await update.message.reply_text(f"{len(bo_so)} số càng:\n{result}")
        context.user_data['wait_for_cang_input'] = False
        await menu(update, context)
        return

    # Đảo số
    if context.user_data.get('wait_for_daoso'):
        s = update.message.text.strip()
        arr = split_numbers(s)
        s_concat = ''.join(arr) if arr else s.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (ví dụ 1234, 56789).")
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}")
        context.user_data['wait_for_daoso'] = False
        await menu(update, context)
        return

    # Phong thủy theo ngày dương
    if context.user_data.get('wait_phongthuy_ngay_duong'):
        ngay = update.message.text.strip()
        try:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if sohap_info is None:
                await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp cho ngày này!")
            else:
                text = phong_thuy_format(can_chi, sohap_info)
                await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("❗️ Nhập ngày không hợp lệ! Đúng định dạng YYYY-MM-DD.")
        context.user_data['wait_phongthuy_ngay_duong'] = False
        await menu(update, context)
        return

    # Phong thủy theo can chi
    if context.user_data.get('wait_phongthuy_ngay_canchi'):
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if sohap_info is None:
            await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp với tên bạn nhập! Kiểm tra lại định dạng (VD: Giáp Tý).")
        else:
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown")
        context.user_data['wait_phongthuy_ngay_canchi'] = False
        await menu(update, context)
        return

    await update.message.reply_text("Bot đã nhận tin nhắn của bạn!")
    await menu(update, context)

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

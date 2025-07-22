from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so
from utils.can_chi_utils import (
    get_can_chi_ngay,
    sinh_so_hap_cho_ngay,
    phong_thuy_format,
    chuan_hoa_can_chi
)
from handlers.menu import get_menu_keyboard, get_xien_keyboard, get_cang_dao_keyboard, get_back_reset_keyboard
from datetime import datetime

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    # ======= GHÉP XIÊN =======
    if 'wait_for_xien_input' in user_data:
        n = user_data['wait_for_xien_input']
        if n is None:
            await update.message.reply_text("Chọn loại xiên:", reply_markup=get_xien_keyboard())
            return
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, n)
        if not xiens:
            await update.message.reply_text("⚠️ Không ghép được xiên, vui lòng nhập lại.", reply_markup=get_xien_keyboard())
        else:
            reply = f"{len(xiens)} bộ xiên {n}:\n" + ', '.join(xiens[:50])
            await update.message.reply_text(reply, reply_markup=get_menu_keyboard())
        user_data.clear()
        return

    # ======= GHÉP CÀNG 3D =======
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 2 chữ số! (VD: 12 34 56)", reply_markup=get_back_reset_keyboard())
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):", reply_markup=get_back_reset_keyboard())
        return

    # ======= GHÉP CÀNG 4D =======
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 3 chữ số! (VD: 123 456)", reply_markup=get_back_reset_keyboard())
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):", reply_markup=get_back_reset_keyboard())
        return

    # ======= XỬ LÝ GHÉP CÀNG SAU KHI ĐÃ CÓ DÀN =======
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers", []) if kind == "3D" else user_data.get("cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await update.message.reply_text("⚠️ Vui lòng nhập ít nhất 1 càng.", reply_markup=get_back_reset_keyboard())
            return
        result = [c + n for c in cangs for n in numbers]
        await update.message.reply_text(f"✅ Ghép {kind}: {len(result)} số\n" + ', '.join(result), reply_markup=get_menu_keyboard())
        user_data.clear()
        return

    # ======= ĐẢO SỐ =======
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        s_concat = ''.join(arr) if arr else msg.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (VD: 1234, 56789).", reply_markup=get_back_reset_keyboard())
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}", reply_markup=get_menu_keyboard())
        user_data.clear()
        return

    # ======= PHONG THỦY SỐ (1 trạng thái) =======
    if user_data.get('wait_phongthuy'):
        # Thử nhận diện là ngày
        try:
            ngay = msg
            for sep in ["-", "/", "."]:
                if sep in ngay:
                    parts = [int(x) for x in ngay.split(sep)]
                    break
            else:
                raise ValueError
            now = datetime.now()
            if len(parts) == 3:
                if parts[0] > 31:
                    y, m, d = parts
                else:
                    d, m, y = parts
            elif len(parts) == 2:
                d, m = parts
                y = now.year
            else:
                raise ValueError
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())
        except Exception:
            # Nếu không phải ngày, thử coi là can chi
            can_chi = chuan_hoa_can_chi(msg)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if sohap_info is None:
                await update.message.reply_text(
                    "❗️ Không tìm thấy thông tin ngày/can chi hoặc sai định dạng! Hãy nhập lại (VD: 2024-07-21 hoặc Giáp Tý).",
                    reply_markup=get_back_reset_keyboard())
                return  # Giữ trạng thái để nhập lại
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())
        user_data["wait_phongthuy"] = False
        return

    # Không ở trạng thái nào → KHÔNG trả lời tin nhắn tự do!
    return

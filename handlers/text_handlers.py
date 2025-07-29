from telegram import Update
from handlers.menu import (
    get_menu_keyboard,
    get_xien_keyboard,
    get_cang_dao_keyboard,
    get_back_reset_keyboard,
    tra_ketqua_theo_ngay
)
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so
from utils.can_chi_utils import (
    sinh_so_hap_cho_ngay,
    phong_thuy_format,
    chuan_hoa_can_chi
)
from datetime import datetime
from handlers.xien import format_xien_result

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    # ======= TRA CỨU KẾT QUẢ XSMB THEO NGÀY =======
    if user_data.get("wait_kq_theo_ngay"):
        result = tra_ketqua_theo_ngay(msg)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=result,
            parse_mode="Markdown",
        )
        user_data.clear()
        return

    # ======= GHÉP XIÊN =======
    if 'wait_for_xien_input' in user_data:
        n = user_data['wait_for_xien_input']
        if n is None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Chọn loại xiên: 2, 3 hoặc 4.",
            )
            return
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, n)
        reply = format_xien_result(xiens)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=reply,
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ======= GHÉP CÀNG 3D =======
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="⚠️ Nhập dàn số 2 chữ số, cách nhau bằng dấu cách. VD: 12 34 56",
            )
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="📥 Nhập các càng muốn ghép (VD: 1 2 3):",
        )
        return

    # ======= GHÉP CÀNG 4D =======
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="⚠️ Nhập dàn số 3 chữ số, cách nhau bằng dấu cách. VD: 123 456",
            )
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="📥 Nhập các càng muốn ghép (VD: 1 2 3):",
        )
        return

    # ======= XỬ LÝ GHÉP CÀNG SAU KHI ĐÃ CÓ DÀN =======
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers", []) if kind == "3D" else user_data.get("cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="⚠️ Vui lòng nhập ít nhất 1 càng (số 1 chữ số).",
            )
            return
        result = [c + n for c in cangs for n in numbers]
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"*✅ Ghép {kind}:* Tổng {len(result)} số\n" + ', '.join(result),
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ======= ĐẢO SỐ =======
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        if not arr or not all(2 <= len(x) <= 6 for x in arr):
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="⚠️ Nhập từng số có 2-6 chữ số, cách nhau bằng dấu cách. VD: 123 4567",
            )
            return
        daos = [dao_so(s) for s in arr]
        text_result = []
        for a, b in zip(arr, daos):
            text_result.append(f"{a}: {', '.join(b)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*ĐẢO SỐ:*\n" + '\n'.join(text_result),
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ======= PHONG THỦY SỐ =======
    if user_data.get("wait_phongthuy"):
        try:
            ngay, canchi = chuan_hoa_can_chi(msg)
            if ngay:
                so_hap = sinh_so_hap_cho_ngay(ngay)
                can, chi = canchi if canchi else (None, None)
                res = phong_thuy_format(can, chi, so_hap, ngay=ngay)
            elif canchi:
                so_hap = sinh_so_hap_cho_ngay(canchi=canchi)
                res = phong_thuy_format(canchi[0], canchi[1], so_hap)
            else:
                res = "❗ Nhập ngày (yyyy-mm-dd hoặc dd-mm) hoặc can chi (VD: Giáp Tý)"
        except Exception as e:
            res = f"Lỗi tra cứu: {e}"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=res,
            parse_mode="Markdown",
        )
        user_data.clear()
        return

    # ======= Ngoài luồng: KHÔNG trả lời =======
    return

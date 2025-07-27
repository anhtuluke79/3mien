from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so
from utils.can_chi_utils import (
    get_can_chi_ngay,
    sinh_so_hap_cho_ngay,
    phong_thuy_format,
    chuan_hoa_can_chi
)
from handlers.menu import (
    get_menu_keyboard,
    get_xien_keyboard,
    get_cang_dao_keyboard,
    get_back_reset_keyboard,
    tra_ketqua_theo_ngay
)
from datetime import datetime

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    # ======= TRA CỨU KẾT QUẢ XSMB THEO NGÀY =======
    if user_data.get("wait_kq_theo_ngay"):
        result = tra_ketqua_theo_ngay(msg)
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            result,
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("ketqua")
        )
        user_data.clear()
        return

    # ======= GHÉP XIÊN =======
    if 'wait_for_xien_input' in user_data:
        n = user_data['wait_for_xien_input']
        if n is None:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "Chọn loại xiên: 2, 3 hoặc 4.",
                reply_markup=get_xien_keyboard()
            )
            return
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, n)
        if not xiens:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "⚠️ Không ghép được xiên, vui lòng nhập lại hoặc chọn loại xiên khác.",
                reply_markup=get_xien_keyboard()
            )
        else:
            reply = f"*{len(xiens)} bộ xiên {n}:*\n" + ', '.join(xiens[:50])
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                reply,
                reply_markup=get_menu_keyboard(),
                parse_mode="Markdown"
            )
        user_data.clear()
        return

    # ======= GHÉP CÀNG 3D =======
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "⚠️ Nhập dàn số 2 chữ số, cách nhau bằng dấu cách. VD: 12 34 56",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ======= GHÉP CÀNG 4D =======
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "⚠️ Nhập dàn số 3 chữ số, cách nhau bằng dấu cách. VD: 123 456",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ======= XỬ LÝ GHÉP CÀNG SAU KHI ĐÃ CÓ DÀN =======
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers", []) if kind == "3D" else user_data.get("cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "⚠️ Vui lòng nhập ít nhất 1 càng (số 1 chữ số).",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        result = [c + n for c in cangs for n in numbers]
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            f"*✅ Ghép {kind}:* Tổng {len(result)} số\n" + ', '.join(result),
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ======= ĐẢO SỐ =======
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        if not arr or not all(2 <= len(x) <= 6 for x in arr):
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                "⚠️ Nhập từng số có 2-6 chữ số, cách nhau bằng dấu cách. VD: 123 4567",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        daos = [dao_so(s) for s in arr]
        text = []
        for a, b in zip(arr, daos):
            text.append(f"{a}: {', '.join(b)}")
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            "*ĐẢO SỐ:*\n" + '\n'.join(text),
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ======= PHONG THỦY SỐ =======
    if user_data.get("wait_phongthuy"):
        try:
            ngay, canchi = chuan_hoa_can_chi(msg)
            if ngay:
                can, chi = get_can_chi_ngay(ngay)
                so_hap = sinh_so_hap_cho_ngay(ngay)
                res = phong_thuy_format(can, chi, so_hap, ngay=ngay)
            elif canchi:
                so_hap = sinh_so_hap_cho_ngay(canchi=canchi)
                res = phong_thuy_format(canchi[0], canchi[1], so_hap)
            else:
                res = "❗ Nhập ngày (yyyy-mm-dd hoặc dd-mm) hoặc can chi (VD: Giáp Tý)"
        except Exception as e:
            res = f"Lỗi tra cứu: {e}"
        await context.bot.send_message(chat_id=update.effective_chat.id, 
            res,
            parse_mode="Markdown",
            reply_markup=get_menu_keyboard()
        )
        user_data.clear()
        return

    # ======= Ngoài luồng: KHÔNG trả lời =======
    return

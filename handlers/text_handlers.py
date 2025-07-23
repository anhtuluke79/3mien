from telegram import Update
from telegram.ext import ContextTypes
import os
from utils.utils import split_numbers, ghep_xien, dao_so
from utils.can_chi_utils import (
    get_can_chi_ngay,
    sinh_so_hap_cho_ngay,
    phong_thuy_format,
    chuan_hoa_can_chi
)
from handlers.menu import (
    get_menu_keyboard, get_admin_keyboard, get_xien_keyboard,
    get_cang_dao_keyboard, get_back_reset_keyboard, ADMIN_IDS
)
from datetime import datetime

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()
    user_id = update.effective_user.id

    # ====== GÓP Ý ======
    if user_data.get("wait_for_gopy"):
        username = update.effective_user.username or update.effective_user.full_name or update.effective_user.id
        with open("gopy_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {username}: {msg}\n")
        await update.message.reply_text(
            "💗 Cảm ơn bạn đã góp ý/ủng hộ bot!\nBạn có thể tiếp tục sử dụng các chức năng khác.",
            reply_markup=get_menu_keyboard(user_id in ADMIN_IDS)
        )
        user_data.clear()
        return

    # ====== ADMIN BROADCAST ======
    if user_data.get("wait_for_broadcast"):
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Bạn không có quyền gửi broadcast.", reply_markup=get_menu_keyboard(False))
            user_data.clear()
            return
        try:
            with open("user_list.txt") as f:
                ids = [int(line.strip()) for line in f if line.strip()]
        except Exception:
            ids = []
        sent = 0
        for uid in ids:
            try:
                await context.bot.send_message(chat_id=uid, text=f"[BROADCAST]\n{msg}")
                sent += 1
            except Exception as e:
                print(f"Lỗi gửi tới {uid}: {e}")
        await update.message.reply_text(f"Đã gửi broadcast tới {sent} user.", reply_markup=get_admin_keyboard())
        user_data.clear()
        return

    # ====== GHÉP XIÊN ======
    if 'wait_for_xien_input' in user_data:
        n = user_data['wait_for_xien_input']
        if n is None:
            await update.message.reply_text(
                "Chọn loại xiên: 2, 3 hoặc 4.",
                reply_markup=get_xien_keyboard()
            )
            return
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, n)
        if not xiens:
            await update.message.reply_text(
                "⚠️ Không ghép được xiên, vui lòng nhập lại hoặc chọn loại xiên khác.",
                reply_markup=get_xien_keyboard()
            )
        else:
            reply = f"*{len(xiens)} bộ xiên {n}:*\n" + ', '.join(xiens[:50])
            await update.message.reply_text(
                reply,
                reply_markup=get_menu_keyboard(user_id in ADMIN_IDS),
                parse_mode="Markdown"
            )
        user_data.clear()
        return

    # ====== GHÉP CÀNG 3D ======
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await update.message.reply_text(
                "⚠️ Nhập dàn số 2 chữ số, cách nhau bằng dấu cách. VD: 12 34 56",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await update.message.reply_text(
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ====== GHÉP CÀNG 4D ======
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await update.message.reply_text(
                "⚠️ Nhập dàn số 3 chữ số, cách nhau bằng dấu cách. VD: 123 456",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await update.message.reply_text(
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ====== XỬ LÝ GHÉP CÀNG SAU KHI ĐÃ CÓ DÀN ======
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers", []) if kind == "3D" else user_data.get("cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await update.message.reply_text(
                "⚠️ Vui lòng nhập ít nhất 1 càng (số 1 chữ số).",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
            return
        result = [c + n for c in cangs for n in numbers]
        await update.message.reply_text(
            f"*✅ Ghép {kind}:* Tổng {len(result)} số\n" + ', '.join(result),
            reply_markup=get_menu_keyboard(user_id in ADMIN_IDS),
            parse_mode="Markdown"
        )
        user_data.clear()
        return

    # ====== ĐẢO SỐ ======
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        s_concat = ''.join(arr) if arr else msg.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text(
                "⚠️ Nhập 1 số từ 2 đến 6 chữ số. VD: 1234",
                reply_markup=get_back_reset_keyboard("ghep_cang_dao")
            )
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(
                f"*Tổng {len(result)} hoán vị:*\n{text}",
                reply_markup=get_menu_keyboard(user_id in ADMIN_IDS),
                parse_mode="Markdown"
            )
        user_data.clear()
        return

    # ====== PHONG THỦY SỐ ======
    if user_data.get('wait_phongthuy'):
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
            await update.message.reply_text(
                text, parse_mode="Markdown", reply_markup=get_menu_keyboard(user_id in ADMIN_IDS)
            )
        except Exception:
            can_chi = chuan_hoa_can_chi(msg)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if sohap_info is None:
                await update.message.reply_text(
                    "❗️ Không tìm thấy thông tin ngày/can chi hoặc sai định dạng!\n"
                    "Hãy nhập lại (VD: 2024-07-23 hoặc Giáp Tý).",
                    reply_markup=get_back_reset_keyboard("menu")
                )
                return
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(
                text, parse_mode="Markdown", reply_markup=get_menu_keyboard(user_id in ADMIN_IDS)
            )
        user_data["wait_phongthuy"] = False
        return

    # Nếu không ở trạng thái nào, không trả lời!
    return

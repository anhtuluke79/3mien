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
)
from datetime import datetime

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()
    lower_msg = msg.lower()

    # Các lệnh đặc biệt luôn cho phép gọi
    if lower_msg in ["menu", "/menu"]:
        await update.message.reply_text("📋 Chọn chức năng:", reply_markup=get_menu_keyboard())
        user_data.clear()
        return
    if lower_msg in ["reset", "/reset"]:
        await update.message.reply_text(
            "🔄 Đã reset trạng thái. Bạn có thể bắt đầu lại bằng lệnh /menu hoặc chọn lại chức năng!",
            reply_markup=get_menu_keyboard()
        )
        user_data.clear()
        return
    if lower_msg in ["hướng dẫn", "huong dan", "ℹ️ hướng dẫn", "/help", "help"]:
        await update.message.reply_text(
            "🟣 HƯỚNG DẪN SỬ DỤNG:\n"
            "- Chọn 'Ghép xiên' để nhập số và chọn loại xiên.\n"
            "- Chọn 'Ghép càng/Đảo số' để ghép càng hoặc đảo số cho dàn đề/lô.\n"
            "- Chọn 'Phong thủy số' để tra cứu số hợp theo ngày hoặc can chi.\n"
            "- Gõ /menu để hiện lại menu chức năng.\n"
            "- Gõ /reset để xóa trạng thái và bắt đầu lại.",
            reply_markup=get_back_reset_keyboard()
        )
        return

    # ======= Chỉ trả lời nếu user đang ở trạng thái nhập liệu =======
    # ======= GHÉP XIÊN =======
    if user_data.get("wait_for_xien_input"):
        do_dai = user_data.pop('wait_for_xien_input')
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, do_dai)
        if not xiens:
            await update.message.reply_text(
                "⚠️ Không ghép được xiên, vui lòng nhập lại hoặc chọn 'Quay lại'.",
                reply_markup=get_xien_keyboard()
            )
        else:
            reply = f"{len(xiens)} bộ xiên {do_dai}:\n" + ', '.join(xiens[:50])
            await update.message.reply_text(reply, reply_markup=get_xien_keyboard())
        return

    # ======= GHÉP CÀNG 3D =======
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await update.message.reply_text(
                "⚠️ Mỗi số cần đúng 2 chữ số! (VD: 12 34 56)",
                reply_markup=get_cang_dao_keyboard()
            )
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await update.message.reply_text(
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard()
        )
        return

    # ======= GHÉP CÀNG 4D =======
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await update.message.reply_text(
                "⚠️ Mỗi số cần đúng 3 chữ số! (VD: 123 456 789)",
                reply_markup=get_cang_dao_keyboard()
            )
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await update.message.reply_text(
            "📥 Nhập các càng muốn ghép (VD: 1 2 3):",
            reply_markup=get_back_reset_keyboard()
        )
        return

    # ======= XỬ LÝ GHÉP CÀNG SAU KHI ĐÃ CÓ DÀN =======
    if user_data.get("wait_cang_input"):
        kind = user_data.pop("wait_cang_input")
        numbers = user_data.pop("cang3d_numbers", []) if kind == "3D" else user_data.pop("cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await update.message.reply_text(
                "⚠️ Vui lòng nhập ít nhất 1 càng.",
                reply_markup=get_back_reset_keyboard()
            )
            return
        result = [c + n for c in cangs for n in numbers]
        await update.message.reply_text(
            f"✅ Ghép {kind}: {len(result)} số\n" + ', '.join(result),
            reply_markup=get_cang_dao_keyboard()
        )
        return

    # ======= ĐẢO SỐ =======
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        s_concat = ''.join(arr) if arr else msg.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text(
                "Nhập 1 số có từ 2 đến 6 chữ số (VD: 1234, 56789).",
                reply_markup=get_cang_dao_keyboard()
            )
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}", reply_markup=get_cang_dao_keyboard())
        user_data.pop("wait_for_dao_input", None)
        return

    # ======= PHONG THỦY SỐ THEO NGÀY =======
    if user_data.get("wait_phongthuy_ngay_duong"):
        ngay = msg
        try:
            for sep in ["-", "/", "."]:
                if sep in ngay:
                    parts = [int(x) for x in ngay.split(sep)]
                    break
            else:
                raise ValueError("Sai định dạng")
            now = datetime.now()
            if len(parts) == 3:
                if parts[0] > 31:  # yyyy-mm-dd
                    y, m, d = parts
                else:
                    d, m, y = parts
            elif len(parts) == 2:
                d, m = parts
                y = now.year
            else:
                raise ValueError("Sai định dạng")
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard())
        except Exception:
            await update.message.reply_text(
                "❗️ Nhập ngày không hợp lệ! Dùng dạng YYYY-MM-DD hoặc DD-MM, ví dụ: 2024-07-22 hoặc 22-07.",
                reply_markup=get_back_reset_keyboard()
            )
        user_data.pop("wait_phongthuy_ngay_duong", None)
        return

    # ======= PHONG THỦY SỐ THEO CAN CHI =======
    if user_data.get("wait_phongthuy_ngay_canchi"):
        can_chi = chuan_hoa_can_chi(msg)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if sohap_info is None:
            await update.message.reply_text(
                "❗️ Không tìm thấy thông tin can chi hoặc số hạp với tên bạn nhập! Kiểm tra lại định dạng (VD: Giáp Tý).",
                reply_markup=get_back_reset_keyboard()
            )
        else:
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard())
        user_data.pop("wait_phongthuy_ngay_canchi", None)
        return

    # ======= Nếu không nằm trong trạng thái, bot sẽ im lặng =======
    return

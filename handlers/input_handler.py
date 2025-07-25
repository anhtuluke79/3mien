from telegram import Update
from telegram.ext import ContextTypes
from handlers.xien import clean_numbers_input, gen_xien, format_xien_result
from handlers.cang_dao import ghep_cang, dao_so
from handlers.kq import tra_ketqua_theo_ngay
from handlers.phongthuy import phongthuy_tudong
from handlers.keyboards import get_back_reset_keyboard
from system.admin import log_user_action

@log_user_action("Xử lý nhập tự do")
async def handle_user_free_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    user_data = context.user_data

    # ---- GHÉP XIÊN ----
    if user_data.get("wait_for_xien_input"):
        n = user_data.get("wait_for_xien_input")
        numbers = clean_numbers_input(text)
        combos = gen_xien(numbers, n)
        result = format_xien_result(combos)
        await update.message.reply_text(result, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"))
        user_data["wait_for_xien_input"] = None
        return

    # ---- GHÉP CÀNG 3D ----
    if user_data.get("wait_cang3d_numbers"):
        numbers = clean_numbers_input(text)
        result = ghep_cang(numbers, "3")
        msg = "Kết quả ghép càng 3D:\n" + ", ".join(result)
        await update.message.reply_text(msg, reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"))
        user_data["wait_cang3d_numbers"] = None
        return

    # ---- GHÉP CÀNG 4D ----
    if user_data.get("wait_cang4d_numbers"):
        numbers = clean_numbers_input(text)
        result = ghep_cang(numbers, "4")
        msg = "Kết quả ghép càng 4D:\n" + ", ".join(result)
        await update.message.reply_text(msg, reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"))
        user_data["wait_cang4d_numbers"] = None
        return

    # ---- ĐẢO SỐ ----
    if user_data.get("wait_for_dao_input"):
        so = text
        result = dao_so(so)
        if result:
            msg = "Tất cả hoán vị:\n" + ", ".join(result)
        else:
            msg = "❗ Nhập số hợp lệ (2-6 chữ số)!"
        await update.message.reply_text(msg, reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"))
        user_data["wait_for_dao_input"] = None
        return

    # ---- TRA KẾT QUẢ XSMB THEO NGÀY ----
    if user_data.get("wait_kq_theo_ngay"):
        ketqua = tra_ketqua_theo_ngay(text)
        await update.message.reply_text(ketqua, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("ketqua"))
        user_data["wait_kq_theo_ngay"] = None
        return

    # ---- PHONG THỦY ----
    if user_data.get("wait_phongthuy"):
        res = phongthuy_tudong(text)
        await update.message.reply_text(res, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("menu"))
        user_data["wait_phongthuy"] = None
        return

    # ---- Không khớp trạng thái nào, không trả lời ----
    # Bạn có thể cho 1 reply mặc định hướng dẫn người dùng chọn lại từ menu nếu muốn:
    # await update.message.reply_text("Vui lòng chọn lại chức năng từ menu bên dưới.", reply_markup=get_menu_keyboard(update.effective_user.id))

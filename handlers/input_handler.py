from telegram import Update
from telegram.ext import ContextTypes
from handlers.xien import clean_numbers_input, gen_xien, format_xien_result
from handlers.cang_dao import ghep_cang, dao_so, clean_numbers_input as clean_input_cang
from handlers.kq import tra_ketqua_theo_ngay
from handlers.phongthuy import phongthuy_tudong
from system.admin import log_user_action
from handlers.keyboards import get_back_reset_keyboard

@log_user_action("Xử lý nhập tự do")
async def handle_user_free_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ---- GHÉP XIÊN ----
    if context.user_data.get("wait_for_xien_input"):
        n = context.user_data.get("wait_for_xien_input")
        numbers = clean_numbers_input(text)
        combos = gen_xien(numbers, n)
        result = format_xien_result(combos)
        await update.message.reply_text(
            result, parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("ghep_xien")
        )
        context.user_data["wait_for_xien_input"] = None
        return

    # ---- GHÉP CÀNG 3D: Nhập dàn số trước ----
    if context.user_data.get("wait_cang3d_numbers"):
        numbers = clean_input_cang(text)
        context.user_data["danh_sach_cang_so"] = [n.zfill(2) for n in numbers if n.isdigit()]
        context.user_data["wait_cang3d_numbers"] = None
        context.user_data["wait_cang3d_cang"] = True
        await update.message.reply_text(
            "Nhập càng muốn ghép (cách nhau bởi dấu cách, phẩy... VD: 0 1 2):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ---- GHÉP CÀNG 3D: Nhập dàn càng ----
    if context.user_data.get("wait_cang3d_cang"):
        cangs = clean_input_cang(text)
        numbers = context.user_data.get("danh_sach_cang_so", [])
        result = ghep_cang(numbers, cangs)
        msg = "Kết quả ghép càng 3D:\n" + ", ".join(result)
        await update.message.reply_text(
            msg, reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data["wait_cang3d_cang"] = None
        context.user_data["danh_sach_cang_so"] = []
        return

    # ---- GHÉP CÀNG 4D: Nhập dàn số trước ----
    if context.user_data.get("wait_cang4d_numbers"):
        numbers = clean_input_cang(text)
        context.user_data["danh_sach_cang_so"] = [n.zfill(3) for n in numbers if n.isdigit()]
        context.user_data["wait_cang4d_numbers"] = None
        context.user_data["wait_cang4d_cang"] = True
        await update.message.reply_text(
            "Nhập càng muốn ghép (cách nhau bởi dấu cách, phẩy... VD: 0 1 2):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        return

    # ---- GHÉP CÀNG 4D: Nhập dàn càng ----
    if context.user_data.get("wait_cang4d_cang"):
        cangs = clean_input_cang(text)
        numbers = context.user_data.get("danh_sach_cang_so", [])
        result = ghep_cang(numbers, cangs)
        msg = "Kết quả ghép càng 4D:\n" + ", ".join(result)
        await update.message.reply_text(
            msg, reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data["wait_cang4d_cang"] = None
        context.user_data["danh_sach_cang_so"] = []
        return

    # ---- ĐẢO SỐ ----
    if context.user_data.get("wait_for_dao_input"):
        so = text
        result = dao_so(so)
        if result:
            msg = "Tất cả hoán vị:\n" + ", ".join(result)
        else:
            msg = "❗ Nhập số hợp lệ (2-6 chữ số)!"
        await update.message.reply_text(
            msg, reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data["wait_for_dao_input"] = None
        return

    # ---- TRA KẾT QUẢ XSMB THEO NGÀY ----
    if context.user_data.get("wait_kq_theo_ngay"):
        ketqua = tra_ketqua_theo_ngay(text)
        await update.message.reply_text(
            ketqua, parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("ketqua")
        )
        context.user_data["wait_kq_theo_ngay"] = None
        return

    # ---- PHONG THỦY ----
    if context.user_data.get("wait_phongthuy"):
        res = phongthuy_tudong(text)
        await update.message.reply_text(
            res, parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )
        context.user_data["wait_phongthuy"] = None
        return

    # ---- Không khớp gì, bỏ qua hoặc có thể nhắc lại ----
    # await update.message.reply_text("Vui lòng chọn lại từ menu!", reply_markup=get_back_reset_keyboard("menu"))

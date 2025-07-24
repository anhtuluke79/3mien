from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import (
    get_menu_keyboard,
    get_ketqua_keyboard,
    get_back_reset_keyboard,
    get_thongke_keyboard,
    get_xien_keyboard,
    get_cang_dao_keyboard
)
from system.admin import admin_callback_handler, admin_menu, ADMIN_IDS
from handlers.ungho import ung_ho_gop_y
from handlers.kq import tra_ketqua_theo_ngay, tra_ketqua_moi_nhat
from utils.thongkemb import (
    read_xsmb,
    thongke_so_ve_nhieu_nhat,
    thongke_lo_gan,
    thongke_dau_cuoi,
    thongke_chan_le,
    goi_y_du_doan
)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    # Xóa trạng thái chờ nhập để tránh lỗi input tự do không mong muốn
    context.user_data.clear()

    # --- ADMIN ---
    if data == "admin_menu":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text(
                "⛔ Bạn không có quyền truy cập menu quản trị!",
                reply_markup=get_menu_keyboard(user_id)
            )
        else:
            await admin_menu(update, context)
        return
    if data.startswith("admin_"):
        await admin_callback_handler(update, context)
        return

    # --- MENU CHÍNH ---
    if data == "menu":
        await menu(update, context)

    # --- KẾT QUẢ ---
    elif data == "ketqua":
        await query.edit_message_text(
            "*🎲 Truy xuất kết quả XSMB*\nChọn chức năng bên dưới:",
            reply_markup=get_ketqua_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "kq_theo_ngay":
        await query.edit_message_text(
            "Nhập ngày bạn muốn tra (có thể nhập: 23-07, 23/07, 2025-07-23, 23.07.2025, 2025/07/23...):",
            reply_markup=get_back_reset_keyboard("ketqua"),
            parse_mode="Markdown"
        )
        context.user_data["wait_kq_theo_ngay"] = True
    elif data == "kq_moi_nhat":
        text = await tra_ketqua_moi_nhat()
        await query.edit_message_text(
            text,
            reply_markup=get_back_reset_keyboard("ketqua"),
            parse_mode="Markdown"
        )

    # --- ỦNG HỘ/GÓP Ý ---
    elif data == "ung_ho_gop_y":
        await ung_ho_gop_y(update, context)

    # --- GHÉP XIÊN ---
    elif data == "ghep_xien":
        await query.edit_message_text(
            "*🔢 Ghép xiên* — Nhập dàn số cách nhau bằng dấu cách, phẩy hoặc xuống dòng.\n"
            "Ví dụ: 12 34 56 78\nSau đó chọn loại xiên.",
            reply_markup=get_xien_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['wait_for_xien_input'] = None

    elif data in ["xien2", "xien3", "xien4"]:
        n = int(data[-1])
        context.user_data['wait_for_xien_input'] = n
        await query.edit_message_text(
            f"*🔢 Ghép xiên {n}* — Nhập dàn số cách nhau bằng dấu cách, phẩy hoặc xuống dòng:",
            reply_markup=get_back_reset_keyboard("ghep_xien"),
            parse_mode="Markdown"
        )

    # --- GHÉP CÀNG/ĐẢO SỐ ---
    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "*🎯 Ghép càng/Đảo số* — Chọn chức năng bên dưới:",
            reply_markup=get_cang_dao_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "ghep_cang3d":
        await query.edit_message_text(
            "Nhập dàn số 2 chữ số (VD: 12 34 56):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_cang3d_numbers'] = True
    elif data == "ghep_cang4d":
        await query.edit_message_text(
            "Nhập dàn số 3 chữ số (VD: 123 456 789):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_cang4d_numbers'] = True
    elif data == "dao_so":
        await query.edit_message_text(
            "Nhập 1 số bất kỳ (2-6 chữ số, VD: 1234):",
            reply_markup=get_back_reset_keyboard("ghep_cang_dao")
        )
        context.user_data['wait_for_dao_input'] = True

    # --- PHONG THỦY ---
    elif data == "phongthuy":
        await query.edit_message_text(
            "🔮 *PHONG THỦY SỐ*\n"
            "- Nhập ngày dương (VD: 2025-07-23 hoặc 23-07)\n"
            "- Hoặc nhập can chi (VD: Giáp Tý, Ất Mão)\n"
            "— Kết quả gồm can, mệnh, số hạp.",
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )
        context.user_data["wait_phongthuy"] = True

    # --- RESET ---
    elif data == "reset":
        context.user_data.clear()
        text = "🔄 *Đã reset trạng thái.*\nQuay lại menu chính để bắt đầu mới!"
        await query.edit_message_text(
            text,
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

    # --- HƯỚNG DẪN ---
    elif data == "huongdan":
        text = (
            "🟣 *HƯỚNG DẪN NHANH:*\n"
            "— *Ghép xiên*: Nhập dàn số bất kỳ, chọn loại xiên 2-3-4, bot sẽ trả mọi tổ hợp xiên.\n"
            "— *Ghép càng/Đảo số*: Nhập dàn số 2 hoặc 3 chữ số, nhập càng muốn ghép, hoặc đảo số từ 2-6 chữ số.\n"
            "— *Phong thủy số*: Tra cứu số hợp theo ngày dương hoặc can chi (VD: 2025-07-23 hoặc Giáp Tý).\n"
            "— *Kết quả*: Xem xổ số miền Bắc mới nhất hoặc theo ngày.\n"
            "— *Thống kê*: Xem các số nổi bật, lô gan, đầu đuôi, chẵn lẻ, dự đoán vui...\n"
            "— Luôn có nút menu trở lại, reset trạng thái, hoặc gõ /menu để quay về ban đầu."
        )
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_menu_keyboard(user_id)
        )

    # --- THỐNG KÊ ---
    elif data == "thongke_menu":
        await query.edit_message_text(
            "*📊 Chọn một thống kê bên dưới:*",
            reply_markup=get_thongke_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "topve":
        df = read_xsmb()
        res = thongke_so_ve_nhieu_nhat(df, n=30, top=10, bot_only=False)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )
    elif data == "topkhan":
        df = read_xsmb()
        res = thongke_so_ve_nhieu_nhat(df, n=30, top=10, bot_only=True)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )
    elif data == "dau_cuoi":
        df = read_xsmb()
        res = thongke_dau_cuoi(df, n=30)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )
    elif data == "chanle":
        df = read_xsmb()
        res = thongke_chan_le(df, n=30)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )
    elif data == "logan":
        df = read_xsmb()
        res = thongke_lo_gan(df, n=30)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )
    elif data == "goiy":
        df = read_xsmb()
        res = goi_y_du_doan(df, n=30)
        await query.edit_message_text(
            res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown"
        )

    # --- DỰ PHÒNG: Không xác định ---
    else:
        await query.edit_message_text(
            "❓ Không xác định chức năng.",
            reply_markup=get_menu_keyboard(user_id)
        )

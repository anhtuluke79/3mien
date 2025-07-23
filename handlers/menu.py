from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.kq import tra_ketqua_theo_ngay, tra_ketqua_moi_nhat, format_xsmb_ketqua
from handlers.xien import gen_xien, format_xien_result
from handlers.cang_dao import ghep_cang, dao_so
from handlers.phongthuy import phongthuy_ngay, phongthuy_can_chi
from utils import thongkemb as tk
from system.admin import ADMIN_IDS, log_user_action, admin_callback_handler, admin_menu, get_admin_menu_keyboard

# ==== MENU UI ====

def get_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên (Tổ hợp số)", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Kết quả", callback_data="ketqua")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_menu")],
        [InlineKeyboardButton("💖 Ủng hộ / Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛡️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_ketqua_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Kết quả theo ngày", callback_data="kq_theo_ngay")],
        [InlineKeyboardButton("🔥 Kết quả mới nhất", callback_data="kq_moi_nhat")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_thongke_keyboard():
    keyboard = [
        [InlineKeyboardButton("📈 Top số về nhiều nhất", callback_data="topve")],
        [InlineKeyboardButton("📉 Top số về ít nhất", callback_data="topkhan")],
        [InlineKeyboardButton("🔢 Thống kê đầu/đuôi ĐB", callback_data="dau_cuoi")],
        [InlineKeyboardButton("♻️ Chẵn/lẻ ĐB", callback_data="chanle")],
        [InlineKeyboardButton("🚨 Dàn lô gan", callback_data="logan")],
        [InlineKeyboardButton("🎯 Gợi ý dự đoán", callback_data="goiy")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard(menu_callback="menu"):
    keyboard = [
        [InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==== MENU HANDLER ====

@log_user_action("Mở menu chính")
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")

# ==== CALLBACK HANDLER ====

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    context.user_data.clear()

    # --- ADMIN ---
    if data == "admin_menu":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Bạn không có quyền truy cập menu quản trị!", reply_markup=get_menu_keyboard(user_id))
        else:
            await admin_menu(update, context)
        return
    if data.startswith("admin_"):
        await admin_callback_handler(update, context)
        return

    # --- MENU CHÍNH ---
    if data == "menu":
        await menu(update, context)
    elif data == "ketqua":
        await query.edit_message_text(
            "*🎲 Truy xuất kết quả XSMB*\nChọn chức năng bên dưới:",
            reply_markup=get_ketqua_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "kq_theo_ngay":
        await query.edit_message_text(
            "Nhập ngày bạn muốn tra (vd: 23-07, 2025-07-23, ...):",
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
    elif data == "thongke_menu":
        await query.edit_message_text(
            "*📊 Chọn một thống kê bên dưới:*",
            reply_markup=get_thongke_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "topve":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=False)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "topkhan":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=True)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "dau_cuoi":
        df = tk.read_xsmb()
        res = tk.thongke_dau_cuoi(df, n=60)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "chanle":
        df = tk.read_xsmb()
        res = tk.thongke_chan_le(df, n=60)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "logan":
        df = tk.read_xsmb()
        res = tk.thongke_lo_gan(df, n=60)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "goiy":
        df = tk.read_xsmb()
        res = tk.goi_y_du_doan(df, n=60)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    # ...Các nhánh cho ghép xiên, phong thủy, góp ý, help... tiếp tục như cũ
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(user_id))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# === MENU CHÍNH ===
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Nếu có quyền admin/super admin, check ở context hoặc biến môi trường
    is_super_admin = context.user_data.get("is_super_admin", False)
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng 3D", callback_data="menu_cang3d")],
        [InlineKeyboardButton("🎯 Ghép càng 4D", callback_data="menu_cang4d")],
        [InlineKeyboardButton("🔀 Đảo số", callback_data="menu_daoso")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("🔢 Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    if is_super_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
        keyboard.append([InlineKeyboardButton("🗂 Backup/Restore", callback_data="backup_restore_menu")])
        keyboard.append([InlineKeyboardButton("👥 Quản lý user", callback_data="user_manage_menu")])
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

# === CALLBACK CHO MENU CHÍNH VÀ CÁC MENU CON ===
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # -- GHÉP XIÊN --
    if data == "menu_ghepxien":
        context.user_data["mode"] = "xiens"
        context.user_data["do_dai_xien"] = 2  # mặc định xiên 2, có thể mở rộng chọn xiên 3,4
        await query.edit_message_text("Nhập dãy số để ghép xiên (ví dụ: 12 34 56):")
        return

    # -- GHÉP CÀNG 3D --
    if data == "menu_cang3d":
        context.user_data["mode"] = "cang3d"
        context.user_data["cang3d_numbers"] = []
        await query.edit_message_text("Nhập dãy số 2 chữ số (cách nhau khoảng trắng):")
        return

    # -- GHÉP CÀNG 4D --
    if data == "menu_cang4d":
        context.user_data["mode"] = "cang4d"
        context.user_data["cang4d_numbers"] = []
        await query.edit_message_text("Nhập dãy số 3 chữ số (cách nhau khoảng trắng):")
        return

    # -- ĐẢO SỐ --
    if data == "menu_daoso":
        context.user_data["mode"] = "daoso"
        await query.edit_message_text("Nhập 1 số từ 2 đến 6 chữ số (vd: 1234):")
        return

    # -- PHONG THỦY --
    if data == "phongthuy_ngay":
        context.user_data["mode"] = "phongthuy"
        await query.edit_message_text("Nhập ngày dương (YYYY-MM-DD) hoặc can chi (Giáp Tý):")
        return

    # -- CHỐT SỐ --
    if data == "menu_chotso":
        # Tùy logic, ở đây chuyển sang mode "chotso", bạn có thể mở rộng
        context.user_data["mode"] = "chotso"
        await query.edit_message_text("Nhập ngày muốn chốt số (YYYY-MM-DD hoặc DD-MM):")
        return

    # -- THỐNG KÊ --
    if data == "thongke_xsmb":
        context.user_data["mode"] = "xsmb"
        await query.edit_message_text("Đang thống kê XSMB, vui lòng đợi...")
        return

    if data == "thongke_dauduoi":
        context.user_data["mode"] = "thongke"
        context.user_data["submode"] = "dauduoi"
        await query.edit_message_text("Đang thống kê đầu-đuôi đặc biệt, vui lòng đợi...")
        return

    # -- ỦNG HỘ --
    if data == "ungho":
        await query.edit_message_text(
            "💗 Ủng hộ bot qua Vietcombank: 0071003914986 (Trương Anh Tú) hoặc Momo: 0904123123.\n"
            "Xin cảm ơn bạn đã ủng hộ bot phát triển!"
        )
        return

    # -- QUAY LẠI MENU --
    if data == "main_menu":
        await menu(update, context)
        return

    # -- Nếu không khớp, mặc định về menu --
    await menu(update, context)

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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ Ghép số", callback_data="submenu_ghepsos")],
        # ... các nút khác
    ]
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update, context):
    query = update.callback_query
    await query.answer()

    # === GHÉP SỐ (SUBMENU) ===
    if query.data == "submenu_ghepsos":
        keyboard = [
            [InlineKeyboardButton("Ghép xiên", callback_data="submenu_xien")],
            [InlineKeyboardButton("Ghép càng", callback_data="submenu_cang")],
            [InlineKeyboardButton("Đảo số", callback_data="submenu_daoso")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
        ]
        await query.edit_message_text("🔢 Chọn kiểu ghép số:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # === GHÉP XIÊN SUBMENU ===
    if query.data == "submenu_xien":
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="xien2")],
            [InlineKeyboardButton("Xiên 3", callback_data="xien3")],
            [InlineKeyboardButton("Xiên 4", callback_data="xien4")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="submenu_ghepsos")]
        ]
        await query.edit_message_text("Chọn loại xiên:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data in ["xien2", "xien3", "xien4"]:
        context.user_data["mode"] = "xiens"
        context.user_data["xien_type"] = int(query.data[-1])
        await query.edit_message_text(f"Nhập dãy số (ghép xiên {query.data[-1]}, cách nhau khoảng trắng hoặc phẩy):")
        return

    # === GHÉP CÀNG SUBMENU ===
    if query.data == "submenu_cang":
        keyboard = [
            [InlineKeyboardButton("Càng 3D", callback_data="cang3d")],
            [InlineKeyboardButton("Càng 4D", callback_data="cang4d")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="submenu_ghepsos")]
        ]
        await query.edit_message_text("Chọn loại càng:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data in ["cang3d", "cang4d"]:
        context.user_data["mode"] = query.data
        await query.edit_message_text("Nhập dãy số cần ghép càng (cách nhau khoảng trắng hoặc phẩy, vd: 23 32 28 ...):")
        return

    # === ĐẢO SỐ ===
    if query.data == "submenu_daoso":
        context.user_data["mode"] = "daoso"
        await query.edit_message_text("Nhập 1 số hoặc dãy số để đảo hoán vị (vd: 1234):")
        return

    # === QUAY LẠI MENU CHÍNH ===
    if query.data == "main_menu":
        context.user_data["mode"] = None
        await menu(update, context)
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

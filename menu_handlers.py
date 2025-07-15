from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ========== MENU CHÍNH ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_super_admin = context.user_data.get("is_super_admin", False)
    keyboard = [
        [InlineKeyboardButton("➕ Ghép số", callback_data="submenu_ghepsos")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="submenu_phongthuy")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="submenu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="submenu_thongke")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="submenu_ungho")],
    ]
    if is_super_admin:
        keyboard.append([InlineKeyboardButton("👥 Quản lý user", callback_data="submenu_usermanage")])
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
    keyboard.append([InlineKeyboardButton("⬅️ Thoát", callback_data="exit")])
    msg = "🔹 Chọn chức năng:"
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ========== MENU CALLBACK ==========
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    # Reset state mỗi khi vào 1 menu chính (tránh bị kẹt state cũ)
    if data in [
        "main_menu", "submenu_ghepsos", "submenu_phongthuy",
        "submenu_chotso", "submenu_thongke"
    ]:
        context.user_data["mode"] = None

    # --- GHÉP SỐ (SUBMENU) ---
    if data == "submenu_ghepsos":
        keyboard = [
            [InlineKeyboardButton("Ghép xiên", callback_data="submenu_xien")],
            [InlineKeyboardButton("Ghép càng", callback_data="submenu_cang")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("➕ *Ghép số*:\nChọn loại ghép:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # --- GHÉP XIÊN SUBMENU ---
    if data == "submenu_xien":
        keyboard = [
            [InlineKeyboardButton("Xiên 2", callback_data="xien2")],
            [InlineKeyboardButton("Xiên 3", callback_data="xien3")],
            [InlineKeyboardButton("Xiên 4", callback_data="xien4")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="submenu_ghepsos")]
        ]
        await query.edit_message_text("🔗 *Ghép xiên* - chọn loại:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data in ["xien2", "xien3", "xien4"]:
        context.user_data["mode"] = "xiens"
        context.user_data["do_dai_xien"] = int(data[-1])  # Ghi nhớ loại xiên
        await query.edit_message_text(f"Nhập dãy số để ghép xiên {data[-1]} (cách nhau khoảng trắng hoặc phẩy):")
        return

    # --- GHÉP CÀNG SUBMENU ---
    if data == "submenu_cang":
        keyboard = [
            [InlineKeyboardButton("Ghép 3D", callback_data="cang3d")],
            [InlineKeyboardButton("Ghép 4D", callback_data="cang4d")],
            [InlineKeyboardButton("Đảo số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="submenu_ghepsos")]
        ]
        await query.edit_message_text("🎯 *Ghép càng* - chọn loại:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data in ["cang3d", "cang4d"]:
        context.user_data["mode"] = data
        context.user_data["wait_for_cang"] = False  # Bắt đầu lại luồng nhập
        await query.edit_message_text(f"Nhập dãy số để ghép {data.upper()} (cách nhau khoảng trắng hoặc phẩy):")
        return

    if data == "daoso":
        context.user_data["mode"] = "daoso"
        await query.edit_message_text("Nhập số hoặc dãy số để đảo (VD: 1234):")
        return

    # --- PHONG THỦY SUBMENU ---
    if data == "submenu_phongthuy":
        keyboard = [
            [InlineKeyboardButton("Phong thủy hôm nay", callback_data="pt_today")],
            [InlineKeyboardButton("Phong thủy theo ngày", callback_data="pt_theongay")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🔮 *Phong thủy* - Chọn kiểu tra cứu:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "pt_today":
        from phongthuy import phongthuy_homnay_handler
        await phongthuy_homnay_handler(update, context)
        return


    if data == "pt_theongay":
        context.user_data["mode"] = "phongthuy"
        await query.edit_message_text("Nhập ngày tra cứu (vd: 15-07-2025, 15-07, 15/7/2025, 15/7):")
        return



    # --- CHỐT SỐ SUBMENU ---
    if data == "submenu_chotso":
        keyboard = [
            [InlineKeyboardButton("Chốt số hôm nay", callback_data="chotso_today")],
            [InlineKeyboardButton("Chốt số theo ngày", callback_data="chotso_ngay")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🎯 *Chốt số*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "chotso_today":
        context.user_data["mode"] = "chotso_today"
        await query.edit_message_text("Đang chốt số hôm nay...")
        return

    if data == "chotso_ngay":
        context.user_data["mode"] = "chotso_ngay"
        await query.edit_message_text("Nhập ngày dương lịch muốn chốt số (YYYY-MM-DD hoặc DD-MM):")
        return

    # --- THỐNG KÊ SUBMENU ---
    if data == "submenu_thongke":
        keyboard = [
            [InlineKeyboardButton("Thống kê cơ bản", callback_data="thongke_xsmb")],
            [InlineKeyboardButton("Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("📊 *Thống kê*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "thongke_xsmb":
        context.user_data["mode"] = "xsmb"
        await query.edit_message_text("Đang thống kê XSMB, vui lòng đợi...")
        return

    if data == "thongke_dauduoi":
        context.user_data["mode"] = "thongke"
        context.user_data["submode"] = "dauduoi"
        await query.edit_message_text("Đang thống kê đầu-đuôi đặc biệt, vui lòng đợi...")
        return

    # --- ỦNG HỘ ---
    if data == "submenu_ungho":
        await query.edit_message_text(
            "💗 Ủng hộ bot qua Vietcombank: 0071003914986 (Trương Anh Tú) hoặc Momo: 0975164416.\n"
            "Xin cảm ơn bạn đã ủng hộ bot phát triển!"
        )
        return

    # --- USER MANAGEMENT ---
    if data == "submenu_usermanage":
        context.user_data["mode"] = "user_manage"
        await query.edit_message_text("👥 Quản lý user: chọn thao tác hoặc nhập lệnh (duyệt, xóa, danh sách)...")
        return

    # --- ADMIN MENU ---
    if data == "admin_menu":
        context.user_data["mode"] = "admin"
        await query.edit_message_text("⚙️ Vào menu quản trị. Chọn thao tác tiếp theo.")
        return

    # === QUAY LẠI MENU CHÍNH hoặc THOÁT ===
    if data == "main_menu" or data == "exit":
        context.user_data["mode"] = None
        await menu(update, context)
        return

    # --- Nếu không khớp, mặc định về menu ---
    context.user_data["mode"] = None
    await menu(update, context)

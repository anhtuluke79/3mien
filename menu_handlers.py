from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ========== MENU CHÍNH ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_super_admin = context.user_data.get("is_super_admin", False)
    keyboard = [
        [InlineKeyboardButton("➕ Ghép số", callback_data="submenu_ghepsos")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="submenu_phongthuy")],
        [InlineKeyboardButton("⬅️ Thoát", callback_data="exit")]
    ]
    if is_super_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Quản trị", callback_data="admin_menu")])
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

    # === GHÉP SỐ (SUBMENU) ===
    if data == "submenu_ghepsos":
        keyboard = [
            [InlineKeyboardButton("Ghép xiên", callback_data="submenu_xien")],
            [InlineKeyboardButton("Ghép càng", callback_data="submenu_cang")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("➕ *Ghép số*:\nChọn loại ghép:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # === GHÉP XIÊN SUBMENU ===
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
        context.user_data["xien_type"] = int(data[-1])
        await query.edit_message_text(f"Nhập dãy số để ghép xiên {data[-1]} (cách nhau khoảng trắng hoặc phẩy):")
        return

    # === GHÉP CÀNG SUBMENU ===
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
        await query.edit_message_text(f"Nhập dãy số để ghép {data.upper()} (cách nhau khoảng trắng hoặc phẩy):")
        return
    if data == "daoso":
        context.user_data["mode"] = "daoso"
        await query.edit_message_text("Nhập số hoặc dãy số để đảo (VD: 1234):")
        return

    # === PHONG THỦY SUBMENU ===
    if data == "submenu_phongthuy":
        keyboard = [
            [InlineKeyboardButton("Phong thủy hôm nay", callback_data="pt_today")],
            [InlineKeyboardButton("Phong thủy theo ngày", callback_data="pt_theongay")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🔮 *Phong thủy* - Chọn kiểu tra cứu:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data == "pt_today":
        context.user_data["mode"] = "phongthuy_today"
        await query.edit_message_text("Đang tra phong thủy hôm nay...")
        # Gọi logic phong thủy hôm nay ở text handler
        return

    if data == "pt_theongay":
        context.user_data["mode"] = "phongthuy_date"
        await query.edit_message_text("Nhập ngày (YYYY-MM-DD) hoặc can chi (VD: Giáp Tý):")
        return

    # === QUAY LẠI MENU CHÍNH ===
    if data == "main_menu" or data == "exit":
        context.user_data["mode"] = None
        await menu(update, context)
        return

    # === MỞ RỘNG: CÁC CHỨC NĂNG KHÁC ===
    # VD: Chốt số, thống kê, ủng hộ... thêm ở đây

    if data == "admin_menu":
        # Gọi tới admin_handlers nếu cần
        await query.edit_message_text("Chức năng quản trị: ... (triển khai riêng)")
        return

    # Nếu không khớp, quay lại menu
    await menu(update, context)

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Xiên 2", callback_data="xien2")],
        [InlineKeyboardButton("🎰 Xiên 3", callback_data="xien3")],
        [InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📍 Chọn chức năng:", reply_markup=reply_markup)


def menu_callback(update, context):
    query = update.callback_query
    query.answer()

    if query.data == "phongthuy":
        query.edit_message_text("🍭 Chức năng phong thủy số.")
    elif query.data == "xien2":
        query.edit_message_text("🎲 Chức năng Xiên 2.")
    elif query.data == "xien3":
        query.edit_message_text("🎰 Chức năng Xiên 3.")
    elif query.data == "xien4":
        query.edit_message_text("✨ Chức năng Xiên 4.")
    else:
        query.edit_message_text("❌ Lựa chọn không hợp lệ.")


menu_handler = CallbackQueryHandler(menu_callback)
        query.edit_message_text("ℹ️ Đây là hướng dẫn sử dụng bot...")
    elif query.data == "reset":
        query.edit_message_text("🔄 Đã reset menu.")
        menu(update, context)


# Đăng ký callback
menu_handler = CallbackQueryHandler(menu_callback)
        query.edit_message_text("🔮 Chức năng phong thủy số.")
    elif data == "thongke":
        query.edit_message_text("📊 Thống kê & AI.")
    elif data == "ungho":
        query.edit_message_text("💖 Cảm ơn bạn đã ủng hộ & góp ý!")
    elif data == "huongdan":
        query.edit_message_text("ℹ️ Đây là phần hướng dẫn sử dụng bot.")
    elif data == "reset":
        query.edit_message_text(
            "📋 Chào mừng bạn đến với Trợ lý Xổ số & AI!",
            reply_markup=get_main_menu()
        )
         InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")],
        [InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d"),
         InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d")],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ])

def get_tk_ai_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🤖 AI Random Forest (dự đoán)", callback_data="ai_rf_choose_n")],
        [InlineKeyboardButton("📈 Top số về nhiều nhất", callback_data="topve")],
        [InlineKeyboardButton("📉 Top số về ít nhất", callback_data="topkhan")],
        [InlineKeyboardButton("🎯 Gợi ý dự đoán", callback_data="goiy")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_rf_ngay_keyboard(for_admin=False):
    prefix = "admin_train_rf_N_" if for_admin else "ai_rf_N_"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("7 ngày", callback_data=f"{prefix}7"),
         InlineKeyboardButton("14 ngày", callback_data=f"{prefix}14")],
        [InlineKeyboardButton("21 ngày", callback_data=f"{prefix}21"),
         InlineKeyboardButton("28 ngày", callback_data=f"{prefix}28")],
        [InlineKeyboardButton("⬅️ Thống kê & AI", callback_data="tk_ai_menu")]
    ])

def get_back_reset_keyboard(menu_callback="menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])

# =========== FORMAT KQ XSMB ===========

def format_xsmb_ketqua(r, ngay_str):
    db = str(r['DB']).strip().zfill(5)
    text = f"🎉 *KQ XSMB {ngay_str}* 🎉\n\n"
    text += f"*Đặc biệt*:   `{db}`\n"
    text += f"*Giải nhất*:  `{str(r['G1']).strip()}`\n"
    for label, col in [
        ("*Giải nhì*", "G2"),
        ("*Giải ba*", "G3"),
        ("*Giải tư*", "G4"),
        ("*Giải năm*", "G5"),
        ("*Giải sáu*", "G6"),
        ("*Giải bảy*", "G7"),
    ]:
        nums = str(r[col]).replace(",", " ").split()
        if len(nums) <= 4:
            text += f"{label}:  " + "  ".join(f"`{n.strip()}`" for n in nums) + "\n"
        else:
            n_half = (len(nums) + 1) // 2
            text += f"{label}:\n"
            text += "  ".join(f"`{n.strip()}`" for n in nums[:n_half]) + "\n"
            text += "  ".join(f"`{n.strip()}`" for n in nums[n_half:]) + "\n"
    return text

def tra_ketqua_theo_ngay(ngay_str):
    try:
        df = pd.read_csv('xsmb.csv')
        date_examples = df['date'].astype(str).head(3).tolist()
        if all('-' in d and len(d.split('-')[0]) == 4 for d in date_examples):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        df['DB'] = df['DB'].astype(str).str.zfill(5)
        day_now = datetime.now()
        try:
            parsed = parser.parse(ngay_str, dayfirst=True, yearfirst=False, default=day_now)
        except Exception:
            return "❗ Định dạng ngày không hợp lệ! Hãy nhập ngày dạng 23-07 hoặc 2025-07-23."
        ngay_input = parsed.replace(hour=0, minute=0, second=0, microsecond=0).date()
        df['date_only'] = df['date'].dt.date
        row = df[df['date_only'] == ngay_input]
        if row.empty:
            return f"⛔ Không có kết quả cho ngày {ngay_input.strftime('%d-%m-%Y')}."
        r = row.iloc[0]
        ngay_str = ngay_input.strftime('%d-%m-%Y')
        return format_xsmb_ketqua(r, ngay_str)
    except Exception as e:
        return f"❗ Lỗi tra cứu: {e}"

async def tra_ketqua_moi_nhat():
    try:
        df = pd.read_csv('xsmb.csv')
        date_examples = df['date'].astype(str).head(3).tolist()
        if all('-' in d and len(d.split('-')[0]) == 4 for d in date_examples):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        df['DB'] = df['DB'].astype(str).str.zfill(5)
        row = df.sort_values('date', ascending=False).iloc[0]
        ngay_str = row['date'].strftime('%d-%m-%Y')
        return format_xsmb_ketqua(row, ngay_str)
    except Exception as e:
        return f"❗ Lỗi tra cứu: {e}"

# ============= MENU CALLBACK HANDLER ==============

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & AI!*"
    if update.message:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    context.user_data.clear()

    if data == "menu":
        await menu(update, context)

    # Kết quả xổ số
    elif data == "ketqua":
        await query.edit_message_text("Chọn chức năng:", reply_markup=get_ketqua_keyboard(), parse_mode="Markdown")
    elif data == "kq_theo_ngay":
        await query.edit_message_text("Nhập ngày muốn tra (23-07, 2025-07-23...):", reply_markup=get_back_reset_keyboard("ketqua"), parse_mode="Markdown")
        context.user_data["wait_kq_theo_ngay"] = True
    elif data == "kq_moi_nhat":
        text = await tra_ketqua_moi_nhat()
        await query.edit_message_text(text, reply_markup=get_back_reset_keyboard("ketqua"), parse_mode="Markdown")

    # Ghép xiên/càng/đảo
    elif data == "ghep_xien_cang_dao":
        await query.edit_message_text("Chọn chức năng:", reply_markup=get_xien_cang_dao_keyboard(), parse_mode="Markdown")
    elif data in ["xien2", "xien3", "xien4"]:
        n = int(data[-1])
        context.user_data['wait_for_xien_input'] = n
        await query.edit_message_text(
            f"Nhập dàn số để ghép xiên {n} (cách nhau bởi dấu cách hoặc phẩy):",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown"
        )
    elif data == "ghep_cang3d":
        context.user_data['wait_cang3d_numbers'] = True
        await query.edit_message_text(
            "Nhập dàn số 2 chữ số để ghép càng 3D (cách nhau bởi dấu cách hoặc phẩy):",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown"
        )
    elif data == "ghep_cang4d":
        context.user_data['wait_cang4d_numbers'] = True
        await query.edit_message_text(
            "Nhập dàn số 3 chữ số để ghép càng 4D (cách nhau bởi dấu cách hoặc phẩy):",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown"
        )
    elif data == "dao_so":
        context.user_data['wait_for_dao_input'] = True
        await query.edit_message_text(
            "Nhập 1 số bất kỳ (2-6 chữ số, VD: 1234):",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown"
        )

    # Phong thủy
    elif data == "phongthuy":
        await query.edit_message_text("Nhập ngày dương hoặc can chi (VD: 2025-07-23, Giáp Tý):", reply_markup=get_back_reset_keyboard("menu"), parse_mode="Markdown")
        context.user_data["wait_phongthuy"] = True

    # Thống kê & AI
    elif data == "tk_ai_menu":
        await query.edit_message_text("*Chọn thống kê hoặc AI:*", reply_markup=get_tk_ai_keyboard(user_id), parse_mode="Markdown")
    elif data == "ai_rf_choose_n":
        await query.edit_message_text("Chọn số ngày để AI Random Forest dự đoán:", reply_markup=get_ai_rf_ngay_keyboard(for_admin=False), parse_mode="Markdown")
        return
    elif data.startswith("ai_rf_N_"):
        N = int(data.split("_")[-1])
        msg = ai_rf.predict_rf_model(num_days=N)
        await query.edit_message_text(msg, reply_markup=get_ai_rf_ngay_keyboard(for_admin=False), parse_mode="Markdown")
        return
    elif data == "topve":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=False)
        await query.edit_message_text(res, reply_markup=get_tk_ai_keyboard(user_id), parse_mode="Markdown")
    elif data == "topkhan":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=True)
        await query.edit_message_text(res, reply_markup=get_tk_ai_keyboard(user_id), parse_mode="Markdown")
    elif data == "goiy":
        df = tk.read_xsmb()
        res = tk.goi_y_du_doan(df, n=60)
        await query.edit_message_text(res, reply_markup=get_tk_ai_keyboard(user_id), parse_mode="Markdown")

    # Ủng hộ/Góp ý, hướng dẫn, reset
    elif data == "ung_ho_gop_y":
        text = (
            "💖 *ỦNG HỘ & GÓP Ý*\n"
            "Cảm ơn bạn đã sử dụng bot! Nếu thấy hữu ích, bạn có thể ủng hộ để mình duy trì bot.\n"
            "Vietcombank: `0071003914986` - TRUONG ANH TU\n"
            "Góp ý: Telegram hoặc email: tutruong19790519@gmail.com\n"
        )
        qr_path = "qr_ung_ho.png"
        await query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_menu_keyboard(user_id)
        )
    elif data == "huongdan":
        text = (
            "🟣 *HƯỚNG DẪN NHANH:*\n"
            "- Kết quả: Xem mới nhất/theo ngày\n"
            "- Ghép xiên/càng/đảo: Tổ hợp các bộ số, ghép càng 3D/4D\n"
            "- Phong thủy: Số hợp mệnh/ngày\n"
            "- Thống kê & AI: Thống kê, AI Random Forest chọn số ngày, gợi ý\n"
            "- Ủng hộ/Góp ý: Nhận phản hồi phát triển\n"
            "- /menu hoặc nút Trở về để về đầu trang"
        )
        await query.edit_message_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
    elif data == "reset":
        context.user_data.clear()
        await query.edit_message_text("🔄 Đã reset trạng thái!", reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")

    # Admin menu
    elif data == "admin_menu":
        await admin_menu(update, context)
        return
    elif data.startswith("admin_"):
        await admin_callback_handler(update, context)
        return
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(user_id))

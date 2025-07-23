from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import pandas as pd
from datetime import datetime

# ===== MENU UI =====

def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên (Tổ hợp số)", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số (Ngày/Can chi)", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Kết quả", callback_data="ketqua")],
        [InlineKeyboardButton("💖 Ủng hộ / Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ketqua_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Kết quả theo ngày", callback_data="kq_theo_ngay")],
        [InlineKeyboardButton("🔥 Kết quả mới nhất", callback_data="kq_moi_nhat")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_xien_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
            InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
            InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")
        ],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cang_dao_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d")],
        [InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d")],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard(menu_callback="menu"):
    keyboard = [
        [InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ====== MENU HANDLERS ======

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🟣 *HƯỚNG DẪN NHANH:*\n"
        "— *Ghép xiên*: Nhập dàn số bất kỳ, chọn loại xiên 2-3-4, bot sẽ trả mọi tổ hợp xiên.\n"
        "— *Ghép càng/Đảo số*: Nhập dàn số 2 hoặc 3 chữ số, nhập càng muốn ghép, hoặc đảo số từ 2-6 chữ số.\n"
        "— *Phong thủy số*: Tra cứu số hợp theo ngày dương hoặc can chi (VD: 2025-07-23 hoặc Giáp Tý).\n"
        "— *Kết quả*: Xem xổ số miền Bắc mới nhất hoặc theo ngày.\n"
        "— Luôn có nút menu trở lại, reset trạng thái, hoặc gõ /menu để quay về ban đầu."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard())

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🔄 *Đã reset trạng thái.*\nQuay lại menu chính để bắt đầu mới!"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(), parse_mode="Markdown")

async def phongthuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "🔮 *PHONG THỦY SỐ*\n"
        "- Nhập ngày dương (VD: 2025-07-23 hoặc 23-07)\n"
        "- Hoặc nhập can chi (VD: Giáp Tý, Ất Mão)\n"
        "— Kết quả gồm can, mệnh, số hạp."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("menu"))
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_back_reset_keyboard("menu"))
    context.user_data["wait_phongthuy"] = True

async def ung_ho_gop_y(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💖 *ỦNG HỘ & GÓP Ý CHO BOT*\n"
        "Cảm ơn bạn đã sử dụng bot! Nếu thấy hữu ích, bạn có thể ủng hộ để mình duy trì và phát triển thêm tính năng.\n\n"
        "🔗 *Chuyển khoản Vietcombank:*\n"
        "`0071003914986`\n"
        "_TRUONG ANH TU_\n\n"
        "Hoặc quét mã QR bên dưới.\n\n"
        "🌟 *Góp ý/đề xuất tính năng*: nhắn trực tiếp qua Telegram hoặc email: tutruong19790519@gmail.com\n"
        "Rất mong nhận được ý kiến của bạn! 😊"
    )
    qr_path = "qr_ung_ho.png"
    await update.callback_query.message.reply_photo(
        photo=open(qr_path, "rb"),
        caption=text,
        parse_mode="Markdown",
        reply_markup=get_menu_keyboard()
    )

# ====== TRA KẾT QUẢ XSMB ======

def tra_ketqua_theo_ngay(ngay_str):
    try:
        df = pd.read_csv('xsmb.csv')
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        if "-" in ngay_str:
            if len(ngay_str) == 5:  # dd-mm
                year = datetime.now().year
                ngay_input = datetime.strptime(f"{ngay_str}-{year}", "%d-%m-%Y")
            else:
                try:
                    ngay_input = datetime.strptime(ngay_str, "%Y-%m-%d")
                except:
                    ngay_input = datetime.strptime(ngay_str, "%d-%m-%Y")
        else:
            return "❗ Định dạng ngày không hợp lệ!"

        row = df[df['date'] == ngay_input]
        if row.empty:
            return f"⛔ Không có kết quả cho ngày {ngay_input.strftime('%d-%m-%Y')}."
        r = row.iloc[0]
        text = f"*KQ XSMB {ngay_input.strftime('%d-%m-%Y')}*\n"
        text += f"ĐB: `{r['DB']}`\nG1: `{r['G1']}`\nG2: `{r['G2']}`\nG3: `{r['G3']}`\nG4: `{r['G4']}`\nG5: `{r['G5']}`\nG6: `{r['G6']}`\nG7: `{r['G7']}`"
        return text
    except Exception as e:
        return f"❗ Lỗi tra cứu: {e}"

async def tra_ketqua_moi_nhat():
    try:
        df = pd.read_csv('xsmb.csv')
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        row = df.sort_values('date', ascending=False).iloc[0]
        text = f"*KQ XSMB {row['date'].strftime('%d-%m-%Y')}*\n"
        text += f"ĐB: `{row['DB']}`\nG1: `{row['G1']}`\nG2: `{row['G2']}`\nG3: `{row['G3']}`\nG4: `{row['G4']}`\nG5: `{row['G5']}`\nG6: `{row['G6']}`\nG7: `{row['G7']}`"
        return text
    except Exception as e:
        return f"❗ Lỗi tra cứu: {e}"

# ====== MENU CALLBACK HANDLER ======

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    context.user_data.clear()
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
            "Nhập ngày bạn muốn tra (dd-mm hoặc yyyy-mm-dd):",
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
    elif data == "ghep_xien":
        await query.edit_message_text(
            "*🔢 Ghép xiên* — Chọn loại xiên muốn ghép:",
            reply_markup=get_xien_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['wait_for_xien_input'] = None
    elif data in ["xien2", "xien3", "xien4"]:
        n = int(data[-1])
        context.user_data['wait_for_xien_input'] = n
        await query.edit_message_text(
            f"*🔢 Ghép xiên {n}* — Nhập dàn số cách nhau bằng dấu cách, phẩy hoặc xuống dòng:",
            reply_markup=get_back_reset_keyboard("ghep_xien"), parse_mode="Markdown"
        )
    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "*🎯 Ghép càng/Đảo số* — Chọn chức năng bên dưới:",
            reply_markup=get_cang_dao_keyboard(), parse_mode="Markdown"
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
    elif data == "phongthuy":
        await phongthuy_command(update, context)
    elif data == "huongdan":
        await help_command(update, context)
    elif data == "reset":
        await reset_command(update, context)
    elif data == "ung_ho_gop_y":
        await ung_ho_gop_y(update, context)
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard())

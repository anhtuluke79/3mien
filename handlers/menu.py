from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import pandas as pd
from datetime import datetime
from dateutil import parser

import utils.thongkemb as tk
import utils.soicau as sc
import utils.ai_rf as ai_rf

# ====== KEYBOARDS ======

def get_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Kết quả", callback_data="ketqua")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_menu")],
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

def get_thongke_keyboard():
    keyboard = [
        [InlineKeyboardButton("🤖 AI Dự đoán (Random Forest)", callback_data="ai_rf")],
        [InlineKeyboardButton("📈 Top số về nhiều nhất", callback_data="topve")],
        [InlineKeyboardButton("📉 Top số về ít nhất", callback_data="topkhan")],
        [InlineKeyboardButton("🔍 Soi cầu/phân tích sâu", callback_data="soicau_menu")],
        [InlineKeyboardButton("🎯 Gợi ý dự đoán", callback_data="goiy")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_soicau_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔥 Số ra liên tục nhiều ngày", callback_data="soicau_lientuc")],
        [InlineKeyboardButton("♻️ Số gan cực đại", callback_data="soicau_ganmax")],
        [InlineKeyboardButton("🔄 Số kép", callback_data="soicau_kep")],
        [InlineKeyboardButton("⬅️ Trở về thống kê", callback_data="thongke_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_reset_keyboard(menu_callback="menu"):
    keyboard = [
        [InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ====== FORMAT KQ XSMB ======

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

# ====== MENU CALLBACK HANDLER ======

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phong thủy!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    context.user_data.clear()
    
    # Menu chính
    if data == "menu":
        await menu(update, context)
    # Thống kê
    elif data == "thongke_menu":
        await query.edit_message_text(
            "*📊 Chọn một thống kê bên dưới:*",
            reply_markup=get_thongke_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "ai_rf":
        df = tk.read_xsmb()
        _, msg = ai_rf.predict_next(df, N=7, top_k=5, retrain=False)
        await query.edit_message_text(msg, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "topve":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=False)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "topkhan":
        df = tk.read_xsmb()
        res = tk.thongke_so_ve_nhieu_nhat(df, n=60, top=10, bot_only=True)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")
    elif data == "goiy":
        df = tk.read_xsmb()
        res = tk.goi_y_du_doan(df, n=60)
        await query.edit_message_text(res, reply_markup=get_thongke_keyboard(), parse_mode="Markdown")

    # === Soi cầu menu và các chức năng ===
    elif data == "soicau_menu":
        await query.edit_message_text(
            "*Chọn chức năng soi cầu:*",
            reply_markup=get_soicau_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "soicau_lientuc":
        df = tk.read_xsmb()
        res = sc.soicau_lientuc(df, n=60)
        await query.edit_message_text(
            res,
            reply_markup=get_soicau_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "soicau_ganmax":
        df = tk.read_xsmb()
        res = sc.soicau_ganmax(df, n=60)
        await query.edit_message_text(
            res,
            reply_markup=get_soicau_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "soicau_kep":
        df = tk.read_xsmb()
        res = sc.soicau_kep(df, n=60)
        await query.edit_message_text(
            res,
            reply_markup=get_soicau_keyboard(),
            parse_mode="Markdown"
        )
    # Kết quả xổ số
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
    # Ghép xiên, càng, đảo số, phong thủy, hướng dẫn...
    elif data == "ghep_xien":
        await query.edit_message_text(
            "*🔢 Ghép xiên* — Nhập dàn số và chọn loại xiên muốn ghép:",
            reply_markup=get_back_reset_keyboard("menu"),
            parse_mode="Markdown"
        )
        context.user_data['wait_for_xien_input'] = None
    elif data == "ghep_cang_dao":
        await query.edit_message_text(
            "*🎯 Ghép càng/Đảo số* — Chọn chức năng bên dưới:",
            reply_markup=get_back_reset_keyboard("menu"), parse_mode="Markdown"
        )
    elif data == "phongthuy":
        await query.edit_message_text(
            "🔮 *PHONG THỦY SỐ*\n- Nhập ngày dương (VD: 2025-07-23 hoặc 23-07)\n- Hoặc nhập can chi (VD: Giáp Tý, Ất Mão)...",
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )
        context.user_data["wait_phongthuy"] = True
    elif data == "huongdan":
        text = (
            "🟣 *HƯỚNG DẪN NHANH:*\n"
            "— *Ghép xiên*: Nhập dàn số bất kỳ, chọn loại xiên 2-3-4, bot sẽ trả mọi tổ hợp xiên.\n"
            "— *Ghép càng/Đảo số*: Nhập dàn số 2 hoặc 3 chữ số, nhập càng muốn ghép, hoặc đảo số từ 2-6 chữ số.\n"
            "— *Phong thủy số*: Tra cứu số hợp theo ngày dương hoặc can chi (VD: 2025-07-23 hoặc Giáp Tý).\n"
            "— *Kết quả*: Xem xổ số miền Bắc mới nhất hoặc theo ngày.\n"
            "— *Thống kê*: Xem các số nổi bật, soi cầu, AI dự đoán, dự đoán vui...\n"
            "— Luôn có nút menu trở lại, reset trạng thái, hoặc gõ /menu để quay về ban đầu."
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_menu_keyboard(user_id))
    elif data == "reset":
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 *Đã reset trạng thái.*\nQuay lại menu chính để bắt đầu mới!",
            reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown"
        )
    elif data == "ung_ho_gop_y":
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
        await query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_menu_keyboard(user_id)
        )
    else:
        await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(user_id))

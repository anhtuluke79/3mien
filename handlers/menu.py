from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import pandas as pd
from datetime import datetime
from dateutil import parser
import utils.thongkemb as tk
import utils.ai_rf as ai_rf
from system.admin import ADMIN_IDS, admin_menu, admin_callback_handler

# ================== KEYBOARDS ==================

def get_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🎲 Kết quả xổ số", callback_data="ketqua")],
        [InlineKeyboardButton("🔢 Ghép xiên/ Càng/ Đảo số", callback_data="ghep_xien_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("📊 Thống kê & AI", callback_data="tk_ai_menu")],
        [InlineKeyboardButton("💖 Ủng hộ & Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛡️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_ketqua_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Kết quả theo ngày", callback_data="kq_theo_ngay")],
        [InlineKeyboardButton("🔥 Kết quả mới nhất", callback_data="kq_moi_nhat")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ])

def get_xien_cang_dao_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
         InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
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

async def format_ketqua(kq_dict):
    formatted = "*Kết quả xổ số:*

"
    for region, values in kq_dict.items():
        formatted += f"*{region}*
"
        for giai, so in values.items():
            formatted += f"`{giai}`: {so}
"
        formatted += "
"
    return formatted

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "☘️ *Chào mừng bạn đến với bot xổ số 3 Miền!* ☘️

Chọn chức năng bên dưới:"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=get_menu_keyboard(user_id),
        parse_mode="Markdown"
    )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu":
        await query.edit_message_text(
            text="☘️ *Chào mừng bạn đến với bot xổ số 3 Miền!* ☘️

Chọn chức năng bên dưới:",
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif data == "ketqua":
        await query.edit_message_text(
            text="Chọn cách xem kết quả:",
            reply_markup=get_ketqua_keyboard()
        )

    elif data == "ghep_xien_cang_dao":
        await query.edit_message_text(
            text="Chọn công cụ xử lý số:",
            reply_markup=get_xien_cang_dao_keyboard()
        )

    elif data == "phongthuy":
        await query.edit_message_text(
            text="🔮 Phong thủy số

Nhập ngày/tháng/năm sinh (ví dụ: 12/05/1990) để xem phân tích:",
            reply_markup=get_back_reset_keyboard("menu")
        )

    elif data == "tk_ai_menu":
        await query.edit_message_text(
            text="📊 Thống kê & AI

Chọn chức năng:",
            reply_markup=get_tk_ai_keyboard(user_id)
        )

    elif data == "ai_rf_choose_n":
        await query.edit_message_text(
            text="🤖 Chọn số ngày để huấn luyện AI Random Forest:",
            reply_markup=get_ai_rf_ngay_keyboard()
        )

    elif data.startswith("ai_rf_N_"):
        n = int(data.split("_")[-1])
        df = ai_rf.load_data()
        predicted = ai_rf.train_and_predict_rf(df, n=n)
        so = ", ".join(predicted)
        await query.edit_message_text(
            text=f"🎯 Kết quả dự đoán (RF-{n} ngày):

*{so}*",
            reply_markup=get_tk_ai_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "reset":
        await query.edit_message_text("✅ Đã reset. Quay lại menu chính.",
                                      reply_markup=get_menu_keyboard(user_id))

    elif data == "huongdan":
        huongdan_text = (
            "🧾 *Hướng dẫn sử dụng bot:*

"
            "- Chọn các chức năng từ menu chính.
"
            "- Dùng các công cụ để xử lý số, xem kết quả, tra phong thủy...
"
            "- Gõ *Reset* để quay lại ban đầu.

"
            "Chúc bạn may mắn!"
        )
        await query.edit_message_text(
            text=huongdan_text,
            parse_mode="Markdown",
            reply_markup=get_back_reset_keyboard("menu")
        )

    elif data == "ung_ho_gop_y":
        await query.edit_message_text(
            text="💖 Cảm ơn bạn đã sử dụng bot!
"
                 "Nếu bạn thấy hữu ích, hãy chia sẻ và đóng góp ý kiến để bot phát triển hơn.",
            reply_markup=get_back_reset_keyboard("menu")
        )

    elif data.startswith("topve"):
        top = tk.thong_ke_top_ve()
        await query.edit_message_text(
            text=f"📈 Top số về nhiều:

{top}",
            reply_markup=get_tk_ai_keyboard()
        )

    elif data.startswith("topkhan"):
        top = tk.thong_ke_top_khan()
        await query.edit_message_text(
            text=f"📉 Top số khan:

{top}",
            reply_markup=get_tk_ai_keyboard()
        )

    elif data == "goiy":
        goiy = tk.goi_y()
        await query.edit_message_text(
            text=f"🎯 Gợi ý hôm nay:

{goiy}",
            reply_markup=get_tk_ai_keyboard()
        )

    elif data.startswith("admin_menu") and user_id in ADMIN_IDS:
        await admin_menu(update, context)

    elif data.startswith("admin_") and user_id in ADMIN_IDS:
        await admin_callback_handler(update, context)
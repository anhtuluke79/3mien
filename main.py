import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters
)
from datetime import datetime
from itertools import combinations, product, permutations

# ========== CẤU HÌNH ==========
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN chưa được thiết lập!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== TIỆN ÍCH SỐ ==========
def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return [' & '.join(comb) for comb in result]

def ghep_cang(numbers, so_cang=3):
    if not numbers or len(numbers) == 0:
        return []
    comb = product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

# ========== MENU CHÍNH ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    keyboard = [
        [InlineKeyboardButton("➕ Ghép Xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép Càng/Đảo Số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong Thủy", callback_data="menu_phongthuy")],
        [InlineKeyboardButton("📈 Thống Kê", callback_data="menu_thongke")],
        [InlineKeyboardButton("🤖 AI & Dự Đoán", callback_data="menu_ai")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Quản trị", callback_data="menu_admin")])
    text = (
        "🌟 <b>MENU CHÍNH</b> 🌟\n\n"
        "Chọn chức năng bên dưới:\n"
        "➕ Ghép Xiên\n"
        "🎯 Ghép Càng/Đảo số\n"
        "🔮 Phong Thủy\n"
        "📈 Thống kê\n"
        "🤖 AI & Dự đoán\n"
    )
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.callback_query.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )

# ========== MENU CALLBACK HANDLER ĐA CẤP ==========
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    is_admin = user_id in ADMIN_IDS

    # Menu GHÉP XIÊN
    if query.data == "menu_ghepxien":
        keyboard = [
            [InlineKeyboardButton("🌱 Xiên 2", callback_data="ghepxien_2")],
            [InlineKeyboardButton("🌿 Xiên 3", callback_data="ghepxien_3")],
            [InlineKeyboardButton("🌳 Xiên 4", callback_data="ghepxien_4")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        text = "➕ <b>Ghép Xiên</b>\nChọn loại xiên:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data in ("ghepxien_2", "ghepxien_3", "ghepxien_4"):
        xiens = {"ghepxien_2":2, "ghepxien_3":3, "ghepxien_4":4}
        context.user_data['wait_for_xien_input'] = xiens[query.data]
        text = f"🌱 Nhập dãy số để ghép xiên {xiens[query.data]} (cách nhau bằng dấu cách hoặc phẩy):"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Ghép Xiên", callback_data="menu_ghepxien")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu GHÉP CÀNG/ĐẢO SỐ
    if query.data == "menu_ghepcang":
        keyboard = [
            [InlineKeyboardButton("🔢 Càng 3D", callback_data="ghepcang_3d")],
            [InlineKeyboardButton("🔢 Càng 4D", callback_data="ghepcang_4d")],
            [InlineKeyboardButton("🔄 Đảo Số", callback_data="daoso")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        text = "🎯 <b>Ghép Càng / Đảo số</b>\nChọn loại:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data in ("ghepcang_3d", "ghepcang_4d"):
        cang = 3 if query.data == "ghepcang_3d" else 4
        context.user_data['wait_for_cang_input'] = cang
        text = f"🔢 Nhập dãy số để ghép càng {cang}D (cách nhau bằng dấu cách hoặc phẩy):"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Ghép Càng", callback_data="menu_ghepcang")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data == "daoso":
        context.user_data['wait_for_daoso'] = True
        text = "🔄 Nhập số cần đảo (ví dụ: 1234):"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Ghép Càng", callback_data="menu_ghepcang")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu PHONG THỦY (CẤP 2)
    if query.data == "menu_phongthuy":
        keyboard = [
            [InlineKeyboardButton("📆 Theo ngày dương", callback_data="menu_phongthuy_duong")],
            [InlineKeyboardButton("📜 Theo can chi", callback_data="menu_phongthuy_canchi")],
            [InlineKeyboardButton("🕰️ Ngày hiện tại", callback_data="phongthuy_ngay_today")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
        ]
        text = "🔮 <b>Phong Thủy</b>\nChọn cách tra cứu:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu PHONG THỦY THEO NGÀY DƯƠNG/CAN CHI (CẤP 3)
    if query.data == "menu_phongthuy_duong":
        context.user_data['wait_phongthuy_ngay_duong'] = True
        text = "📆 Nhập ngày dương (YYYY-MM-DD):"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Phong Thủy", callback_data="menu_phongthuy")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data == "menu_phongthuy_canchi":
        context.user_data['wait_phongthuy_ngay_canchi'] = True
        text = "📜 Nhập can chi (VD: Giáp Tý):"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Phong Thủy", callback_data="menu_phongthuy")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data == "phongthuy_ngay_today":
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        can_chi = "Nhâm Thìn"
        text = (
            f"🔮 <b>Phong thủy NGÀY HIỆN TẠI</b>: {can_chi} ({d:02d}/{m:02d}/{y})\n"
            "- Can: Nhâm, Âm Dương: Dương, Ngũ Hành: Thủy\n"
            "- Số mệnh: 1\n"
            "- Số hạp: 6, 8\n"
            "- Bộ số ghép đặc biệt: 16, 18, 61, 81, 68, 86"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Phong Thủy", callback_data="menu_phongthuy")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu THỐNG KÊ
    if query.data == "menu_thongke":
        text = "📈 <b>Thống kê (giả lập)</b>\n- Top số ĐB: 12 (5 lần)\n- Số ĐB hôm nay: 34"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu AI
    if query.data == "menu_ai":
        keyboard = [
            [InlineKeyboardButton("🤖 Dự đoán AI", callback_data="ai_predict")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        text = "🤖 <b>AI & Dự Đoán</b>\n- Dự đoán số tiếp theo bằng AI (giả lập)\n- Train lại mô hình AI (chỉ admin)"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data == "ai_predict":
        text = "🤖 <b>Kết quả AI dự đoán (giả lập):</b>\nTop 3: 23, 45, 67"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại AI", callback_data="menu_ai")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Menu ADMIN (sâu hơn)
    if query.data == "menu_admin" and is_admin:
        keyboard = [
            [InlineKeyboardButton("🛠️ Update MB", callback_data="capnhat_xsmb_kq"),
             InlineKeyboardButton("🛠️ Update MT", callback_data="capnhat_xsmt_kq")],
            [InlineKeyboardButton("🛠️ Update MN", callback_data="capnhat_xsmn_kq")],
            [InlineKeyboardButton("⚙️ Train AI", callback_data="train_model")],
            [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")]
        ]
        text = "👑 <b>Quản trị dữ liệu</b>\nChọn thao tác (giả lập)"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if query.data.startswith("capnhat_xsm") or query.data == "train_model":
        text = "✅ Đã thực hiện chức năng quản trị (giả lập)!"
        keyboard = [[InlineKeyboardButton("⬅️ Quay lại Quản trị", callback_data="menu_admin")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # Quay lại menu chính
    if query.data == "main_menu":
        await menu(update, context)
        return

# ========== XỬ LÝ TEXT NHẬP ==========
async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # GHÉP XIÊN N
    if isinstance(user_data.get('wait_for_xien_input'), int):
        numbers = split_numbers(text)
        do_dai = user_data.get('wait_for_xien_input')
        bo_xien = ghep_xien(numbers, do_dai)
        if not bo_xien:
            await update.message.reply_text("❗ Không ghép được xiên.")
        else:
            result = ', '.join(bo_xien[:20])
            await update.message.reply_text(f"{len(bo_xien)} bộ xiên:\n{result}")
        user_data['wait_for_xien_input'] = False
        await menu(update, context)
        return

    # GHÉP CÀNG N
    if isinstance(user_data.get('wait_for_cang_input'), int):
        numbers = split_numbers(text)
        so_cang = user_data.get('wait_for_cang_input')
        bo_so = ghep_cang(numbers, so_cang)
        if not bo_so:
            await update.message.reply_text("❗ Không ghép được càng.")
        else:
            result = ', '.join(bo_so[:20])
            await update.message.reply_text(f"{len(bo_so)} số càng:\n{result}")
        user_data['wait_for_cang_input'] = False
        await menu(update, context)
        return

    # ĐẢO SỐ
    if user_data.get('wait_for_daoso'):
        s = text.replace(' ', '')
        if not s.isdigit() or len(s) < 2 or len(s) > 6:
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (ví dụ 1234, 56789).")
        else:
            result = dao_so(s)
            text_rs = ', '.join(result[:30])
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text_rs}")
        user_data['wait_for_daoso'] = False
        await menu(update, context)
        return

    # PHONG THỦY THEO NGÀY DƯƠNG
    if user_data.get('wait_phongthuy_ngay_duong'):
        ngay = text.strip()
        try:
            y, m, d = map(int, ngay.split('-'))
            can_chi = "Nhâm Thìn"
            info = "- Can: Nhâm, Âm Dương: Dương, Ngũ Hành: Thủy\n- Số mệnh: 1\n- Số hạp: 6, 8"
            await update.message.reply_text(
                f"🔮 Phong thủy ngày {can_chi} ({d:02d}/{m:02d}/{y}):\n{info}")
        except Exception:
            await update.message.reply_text("❗ Nhập ngày không hợp lệ! Đúng định dạng YYYY-MM-DD.")
        user_data['wait_phongthuy_ngay_duong'] = False
        await menu(update, context)
        return

    # PHONG THỦY THEO CAN CHI
    if user_data.get('wait_phongthuy_ngay_canchi'):
        can_chi = text.strip().title()
        info = "- Can: Nhâm, Âm Dương: Dương, Ngũ Hành: Thủy\n- Số mệnh: 1\n- Số hạp: 6, 8"
        await update.message.reply_text(f"🔮 Phong thủy ngày {can_chi}:\n{info}")
        user_data['wait_phongthuy_ngay_canchi'] = False
        await menu(update, context)
        return

    # TỪ KHÓA/TÊN BOT/LỆNH
    text_lower = text.lower()
    bot_username = (await context.bot.get_me()).username.lower()
    mention = f"@{bot_username}"
    if (
        mention in text_lower
        or '/menu' in text_lower
        or '/start' in text_lower
        or 'phong thủy' in text_lower
        or 'phong thuy' in text_lower
    ):
        await menu(update, context)
        return

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

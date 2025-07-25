from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from system.admin import ADMIN_IDS, log_user_action, admin_callback_handler, admin_menu
from handlers.keyboards import *
from handlers.input_handler import handle_user_free_input
from utils import ai_rf

# ... các import khác (kq, phongthuy, xien, cang_dao, soicau...)

# ================== KEYBOARD CHO AI ==================
def get_ai_rf_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🤖 Dự đoán 7 ngày", callback_data="ai_rf_predict_7"),
            InlineKeyboardButton("🤖 Dự đoán 14 ngày", callback_data="ai_rf_predict_14"),
        ],
        [
            InlineKeyboardButton("🤖 Dự đoán 21 ngày", callback_data="ai_rf_predict_21"),
            InlineKeyboardButton("🤖 Dự đoán 28 ngày", callback_data="ai_rf_predict_28"),
        ]
    ]
    # Thêm các nút TRAIN cho admin
    keyboard.append([
        InlineKeyboardButton("🛠️ Train 7 ngày", callback_data="ai_rf_train_7"),
        InlineKeyboardButton("🛠️ Train 14 ngày", callback_data="ai_rf_train_14"),
    ])
    keyboard.append([
        InlineKeyboardButton("🛠️ Train 21 ngày", callback_data="ai_rf_train_21"),
        InlineKeyboardButton("🛠️ Train 28 ngày", callback_data="ai_rf_train_28"),
    ])
    keyboard.append([InlineKeyboardButton("⬅️ Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

# ================ MAIN MENU HANDLER ===================
@log_user_action("Mở menu chính")
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số & Phân tích AI!*"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")

# =============== CALLBACK HANDLER ======================
async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    # ... các lệnh menu khác (ketqua, phongthuy, xien, soicau, ...)
    if data == "ai_rf":
        await query.edit_message_text("🤖 *AI Random Forest:*\nChọn chức năng hoặc số ngày:", reply_markup=get_ai_rf_keyboard(), parse_mode="Markdown")
        return

    # TRAIN RF: chỉ admin
    if data.startswith("ai_rf_train_"):
        n = int(data.split("_")[-1])
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Bạn không có quyền train AI!")
            return
        await query.edit_message_text(f"⏳ Đang train Random Forest với {n} ngày, vui lòng đợi…")
        msg = ai_rf.train_rf_model(num_days=n, data_path="xsmb.csv")
        await query.edit_message_text(msg, reply_markup=get_ai_rf_keyboard())
        return

    # DỰ ĐOÁN RF: mọi user đều dùng được
    if data.startswith("ai_rf_predict_"):
        n = int(data.split("_")[-1])
        # Bạn có thể cho người dùng chọn ngày muốn dự đoán hoặc mặc định lấy ngày mới nhất
        msg = ai_rf.predict_rf_model(num_days=n)
        await query.edit_message_text(msg, reply_markup=get_ai_rf_keyboard())
        return

    # ... các nhánh khác (admin, thống kê, vv)
    if data == "admin_menu":
        await admin_menu(update, context)
        return
    if data.startswith("admin_"):
        await admin_callback_handler(update, context)
        return

    # fallback: quay lại menu chính nếu không xác định
    await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(user_id))

# =============== CẬP NHẬT get_menu_keyboard =================
def get_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Kết quả", callback_data="ketqua")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_menu")],
        [InlineKeyboardButton("🎯 Soi cầu", callback_data="soicau_menu")],
        [InlineKeyboardButton("🤖 AI Random Forest", callback_data="ai_rf")],
        [InlineKeyboardButton("💖 Ủng hộ / Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛡️ Quản trị", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

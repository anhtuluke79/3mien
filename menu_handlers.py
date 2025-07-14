from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from logic_xsmb import thong_ke_xsmb, thong_ke_dau_duoi_db, predict_xsmb_rf
from phongthuy import *
from user_manage import is_allowed_user

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [InlineKeyboardButton("🤖 Thần tài dự đoán", callback_data="ml_predict")],
        [InlineKeyboardButton("➕ Ghép xiên", callback_data="menu_ghepxien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="menu_ghepcang")],
        [InlineKeyboardButton("🔮 Phong thủy", callback_data="phongthuy_ngay")],
        [InlineKeyboardButton("🎯 Chốt số", callback_data="menu_chotso")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="thongke_xsmb")],
        [InlineKeyboardButton("🔢 Thống kê đầu-đuôi", callback_data="thongke_dauduoi")],
        [InlineKeyboardButton("💗 Ủng hộ", callback_data="ungho")],
    ]
    # Có thể thêm quyền cho admin hoặc superadmin nếu cần
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🔹 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if not is_allowed_user(user_id):
        await query.edit_message_text("⏳ Bạn chưa được duyệt sử dụng bot, vui lòng chờ admin.")
        return

    if data == "ml_predict":
        await query.edit_message_text("⏳ Đang dự đoán bằng AI Thần tài (Random Forest)...")
        result = predict_xsmb_rf()
        await query.message.reply_text(result)
        await menu(update, context)
        return

    if data == "thongke_xsmb":
        msg = thong_ke_xsmb(15)
        await query.edit_message_text(msg)
        return

    if data == "thongke_dauduoi":
        msg = thong_ke_dau_duoi_db(30)
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    # ...xử lý callback các menu còn lại (phong thủy, chốt số, ghép xiên, đảo số,...)
    # Bạn có thể import và gọi các hàm xử lý tương ứng từ các file riêng

    if data == "main_menu":
        await menu(update, context)
        return

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed_user(user_id):
        await update.message.reply_text("⏳ Bạn chưa được duyệt sử dụng bot, vui lòng chờ admin.")
        return
    # ... Xử lý các tin nhắn nhập số liệu theo context.user_data như đã hướng dẫn ở code gốc
    # Ví dụ: chốt số, ghép càng, đảo số, nhập ngày phong thủy,...
    # Copy các xử lý all_text_handler ở các block code mẫu trước vào đây!

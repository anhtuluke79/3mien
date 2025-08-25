from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


# Hàm tạo menu chính
def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Xiên 2", callback_data="xien2")],
        [InlineKeyboardButton("🎰 Xiên 3", callback_data="xien3")],
        [InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📍 Chọn chức năng:", reply_markup=reply_markup)


# Hàm xử lý khi user bấm nút
def menu_callback(update, context):
    query = update.callback_query
    query.answer()

    if query.data == "huongdan":
        query.edit_message_text("ℹ️ Đây là hướng dẫn sử dụng bot...")
    elif query.data == "phongthuy":
        query.edit_message_text("🔮 Chức năng phong thủy số.")
    elif query.data == "xien2":
        query.edit_message_text("🎲 Chức năng Xiên 2.")
    elif query.data == "xien3":
        query.edit_message_text("🎰 Chức năng Xiên 3.")
    elif query.data == "xien4":
        query.edit_message_text("✨ Chức năng Xiên 4.")
    else:
        query.edit_message_text("❌ Lựa chọn không hợp lệ.")


# Handler callback để import vào main.py
menu_handler = CallbackQueryHandler(menu_callback)

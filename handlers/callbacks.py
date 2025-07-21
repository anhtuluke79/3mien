from telegram import Update
from telegram.ext import ContextTypes
from utils.get_kqxs import get_kqxs
from handlers.menu import get_menu_keyboard, get_back_menu_keyboard

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == 'kqxs_mb':
        msg = get_kqxs('mb')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    elif data == 'kqxs_mn':
        msg = get_kqxs('mn')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    elif data == 'kqxs_mt':
        msg = get_kqxs('mt')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    elif data == 'ghep_xien':
        await query.answer()
        context.user_data['action'] = 'ghep_xien'
        await query.edit_message_text(
            "🔗 *Ghép xiên*: Nhập dãy số cách nhau dấu phẩy (vd: `12,23,34`).",
            parse_mode='Markdown',
            reply_markup=get_back_menu_keyboard())
    elif data == 'ghep_cang':
        await query.answer()
        context.user_data['action'] = 'ghep_cang'
        await query.edit_message_text(
            "🔢 *Ghép càng*: Nhập dãy số cách nhau dấu phẩy (vd: `123,456,789`).",
            parse_mode='Markdown',
            reply_markup=get_back_menu_keyboard())
    elif data == 'dao_so':
        await query.answer()
        context.user_data['action'] = 'dao_so'
        await query.edit_message_text(
            "🔄 *Đảo số*: Nhập số cần đảo (vd: `12345`).",
            parse_mode='Markdown',
            reply_markup=get_back_menu_keyboard())
    elif data == 'back_menu':
        await query.answer()
        await query.edit_message_text(
            "🌟 *Chào mừng trở lại menu!*\nChọn tính năng bạn cần:",
            parse_mode='Markdown',
            reply_markup=get_menu_keyboard())
        context.user_data.clear()
    else:
        await query.answer("Chức năng đang cập nhật.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Admin callback đang cập nhật.")

from telegram import Update
from telegram.ext import ContextTypes
from utils.get_kqxs import get_kqxs

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == 'kqxs_mb':
        msg = get_kqxs('mb')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == 'kqxs_mn':
        msg = get_kqxs('mn')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == 'kqxs_mt':
        msg = get_kqxs('mt')
        await query.answer()
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == 'phongthuy':
        await query.answer("Chức năng đang cập nhật.")
    elif data == 'hotro':
        await query.answer("Liên hệ admin để được hỗ trợ.")
    else:
        await query.answer("Chức năng đang cập nhật.")

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
    elif data == 'ghep_xien':
        await query.answer()
        await query.edit_message_text("🔗 *Ghép xiên*: Vui lòng nhập dãy số bạn muốn ghép xiên (cách nhau dấu phẩy).\n\nVí dụ: `12,23,34`", parse_mode='Markdown')
    elif data == 'ghep_cang':
        await query.answer()
        await query.edit_message_text("🔢 *Ghép càng*: Vui lòng nhập dãy số bạn muốn ghép càng (cách nhau dấu phẩy).\n\nVí dụ: `123,456,789`", parse_mode='Markdown')
    elif data == 'dao_so':
        await query.answer()
        await query.edit_message_text("🔄 *Đảo số*: Vui lòng nhập số cần đảo.\n\nVí dụ: `12345` => Đảo: `54321`", parse_mode='Markdown')
    else:
        await query.answer("Chức năng đang cập nhật.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Admin callback đang cập nhật.")

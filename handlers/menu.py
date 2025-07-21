from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 KQXS Miền Bắc", callback_data='kqxs_mb')],
        [InlineKeyboardButton("🏵️ KQXS Miền Nam", callback_data='kqxs_mn')],
        [InlineKeyboardButton("🌄 KQXS Miền Trung", callback_data='kqxs_mt')],
        [InlineKeyboardButton("🔗 Ghép Xiên", callback_data='ghep_xien')],
        [InlineKeyboardButton("🔢 Ghép Càng", callback_data='ghep_cang')],
        [InlineKeyboardButton("🔄 Đảo Số", callback_data='dao_so')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = (
        "🌟 *Chào mừng đến bot 3 miền!*\n"
        "Chọn tính năng bạn cần:"
    )
    await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

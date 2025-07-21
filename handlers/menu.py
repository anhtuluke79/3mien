from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 KQXS Miền Bắc", callback_data='kqxs_mb')],
        [InlineKeyboardButton("🏵️ KQXS Miền Nam", callback_data='kqxs_mn')],
        [InlineKeyboardButton("🌄 KQXS Miền Trung", callback_data='kqxs_mt')],
        # [InlineKeyboardButton("🔮 Phong thủy", callback_data='phongthuy')],
        # [InlineKeyboardButton("ℹ️ Hỗ trợ", callback_data='hotro')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = (
        "🌟 *Chào mừng đến bot 3 miền!*\n"
        "Chọn tính năng bạn cần:"
    )
    await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

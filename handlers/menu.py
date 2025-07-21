from telegram import Update
from telegram.ext import ContextTypes

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_text = (
        "🌟 *Chào mừng đến bot 3 miền!*\n"
        "\n"
        "• /ketqua — Xem kết quả XSMB mới nhất\n"
        "• /mb — Xổ số miền Bắc\n"
        "• /mn — Xổ số miền Nam\n"
        "• /mt — Xổ số miền Trung\n"
        "• /menu — Hiện menu này\n"
        "\n"
        "_Các chức năng phong thuỷ và tiện ích khác vẫn giữ nguyên!_"
    )
    await update.message.reply_text(menu_text, parse_mode='Markdown')

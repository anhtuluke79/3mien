import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Đảm bảo các handler khác được import nếu cần
from handlers.menu import menu_handler
from handlers.callbacks import callback_handler
from handlers.admin import admin_handler

# Cấu hình log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Hàm crawl kết quả xổ số ---
import requests
from bs4 import BeautifulSoup

def get_kqxs(region='mb'):
    url = {
        'mb': 'https://ketqua.net/xo-so-mien-bac',
        'mn': 'https://ketqua.net/xo-so-mien-nam',
        'mt': 'https://ketqua.net/xo-so-mien-trung'
    }.get(region, 'mb')
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Lấy ngày
    date = soup.find('td', class_='ngay').text.strip()
    # Lấy các giải
    bang = soup.find('table', class_='kqmb' if region=='mb' else 'kqmien')
    rows = bang.find_all('tr')[1:]
    result_lines = [f"*KQXS {'MB' if region=='mb' else ('MN' if region=='mn' else 'MT')} {date}*"]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            label = cells[0].text.strip()
            numbers = ' '.join(c.text.strip() for c in cells[1:])
            result_lines.append(f"{label}: `{numbers}`")
    return '\n'.join(result_lines)

# Lệnh tra cứu kết quả
async def ketqua_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_kqxs('mb')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_kqxs('mn')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_kqxs('mt')
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == '__main__':
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()
    application.add_handler(CommandHandler("start", menu_handler))
    application.add_handler(CommandHandler("menu", menu_handler))
    application.add_handler(CommandHandler("ketqua", ketqua_handler))
    application.add_handler(CommandHandler("mb", ketqua_handler))
    application.add_handler(CommandHandler("mn", mn_handler))
    application.add_handler(CommandHandler("mt", mt_handler))
    # Thêm các handler khác (admin, callback...) nếu cần
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(CommandHandler("callback", callback_handler))
    application.run_polling()

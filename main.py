import os
import requests
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu_handler
from handlers.callbacks import menu_callback_handler
from handlers.input_handler import all_text_handler
from handlers.admin import admin_menu_handler, admin_callback_handler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Chưa thiết lập TELEGRAM_TOKEN!")

# ---- Hàm crawl kết quả xổ số ----
def get_kqxs(region='mb'):
    url = {
        'mb': 'https://ketqua.net/xo-so-mien-bac',
        'mn': 'https://ketqua.net/xo-so-mien-nam',
        'mt': 'https://ketqua.net/xo-so-mien-trung'
    }.get(region, 'mb')
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    date = soup.find('td', class_='ngay').text.strip()
    bang = soup.find('table', class_='kqmb' if region == 'mb' else 'kqmien')
    rows = bang.find_all('tr')[1:]
    result_lines = [f"*KQXS {'MB' if region == 'mb' else ('MN' if region == 'mn' else 'MT')} {date}*"]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            label = cells[0].text.strip()
            numbers = ' '.join(c.text.strip() for c in cells[1:])
            result_lines.append(f"{label}: `{numbers}`")
    return '\n'.join(result_lines)

# ---- Các lệnh xổ số ----
async def ketqua_handler(update, context):
    msg = get_kqxs('mb')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mn_handler(update, context):
    msg = get_kqxs('mn')
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mt_handler(update, context):
    msg = get_kqxs('mt')
    await update.message.reply_text(msg, parse_mode='Markdown')

# ---- Lệnh /start ----
async def start(update, context):
    await update.message.reply_text(
        "✨ Chào mừng bạn đến với XosoBot!\n"
        "• /menu để chọn tính năng\n"
        "• Hoặc chọn chức năng bằng nút phía dưới."
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_menu_handler))

    # Đăng ký các lệnh xổ số
    app.add_handler(CommandHandler("ketqua", ketqua_handler))
    app.add_handler(CommandHandler("mb", ketqua_handler))
    app.add_handler(CommandHandler("mn", mn_handler))
    app.add_handler(CommandHandler("mt", mt_handler))

    # Callback cho admin (nếu còn dùng pattern thì cần hoàn chỉnh, hoặc bỏ nếu không dùng)
    # app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    # Callback cho các menu bình thường
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Xử lý nhập text theo ngữ cảnh thao tác (không trả lời tự do)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()

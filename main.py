from telegram.ext import ApplicationBuilder
from config import TELEGRAM_TOKEN
from handlers import register_handlers

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    register_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()

import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu, menu_callback_handler, help_command, reset_command
from handlers.text_handlers import all_text_handler

TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(TOKEN).build()

# Lệnh
app.add_handler(CommandHandler("start", menu))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("reset", reset_command))

# Nút bấm callback
app.add_handler(CallbackQueryHandler(menu_callback_handler))

# Xử lý tin nhắn văn bản
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))

if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run_polling(close_loop=False))

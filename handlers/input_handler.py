# handlers/input_handler.py

async def all_text_handler(update, context):
    await update.message.reply_text("Bạn vừa gửi: " + update.message.text)

from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    if 'wait_for_xien_input' in user_data:
        do_dai = user_data['wait_for_xien_input']
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, do_dai)
        reply = f"{len(xiens)} bộ xiên {do_dai}:\n" + ', '.join(xiens[:50])  # giới hạn dài
        await update.message.reply_text(reply)
        user_data.clear()
        return

    if 'wait_for_daoso' in user_data:
        s = ''.join(split_numbers(msg))
        if 2 <= len(s) <= 6:
            daos = dao_so(s)
            reply = f"Tổng {len(daos)} hoán vị:\n" + ', '.join(daos[:50])
        else:
            reply = "⚠️ Nhập số có từ 2 đến 6 chữ số."
        await update.message.reply_text(reply)
        user_data.clear()
        return

    # Nếu không có trạng thái nào:
    return

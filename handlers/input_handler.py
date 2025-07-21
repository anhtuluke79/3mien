from telegram import Update
from telegram.ext import ContextTypes
from handlers.menu import get_menu_keyboard, get_back_menu_keyboard

def ghep_xien_logic(nums):
    nums = [n.strip() for n in nums if n.strip()]
    if len(nums) < 2:
        return "Vui lòng nhập ít nhất 2 số để ghép xiên!"
    combos = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            combos.append(f"{nums[i]}-{nums[j]}")
    return "🔗 *Kết quả ghép xiên:*\n" + ', '.join(combos)

def ghep_cang_logic(nums):
    nums = [n.strip() for n in nums if n.strip()]
    if len(nums) < 2:
        return "Vui lòng nhập ít nhất 2 số để ghép càng!"
    combos = []
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j:
                combos.append(nums[i] + nums[j])
    return "🔢 *Kết quả ghép càng:*\n" + ', '.join(combos)

def dao_so_logic(num):
    return "🔄 *Kết quả đảo số:*\n" + num[::-1]

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    text = update.message.text.strip()
    if action == 'ghep_xien':
        nums = text.split(',')
        reply = ghep_xien_logic(nums)
        await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    elif action == 'ghep_cang':
        nums = text.split(',')
        reply = ghep_cang_logic(nums)
        await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    elif action == 'dao_so':
        reply = dao_so_logic(text)
        await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_back_menu_keyboard())
        context.user_data.clear()
    else:
        # KHÔNG trả lời tin nhắn bất kỳ nếu không trong trạng thái đặc biệt
        return
# Để trống hoặc giữ lại các logic tiện ích khác (nếu có)

from telegram import Update
from telegram.ext import ContextTypes
from so_ghép import tao_xien, ghep_cang_3d, ghep_cang_4d, dao_so

# -- Handler nhận text từ user để ghép xiên --
async def xiens_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ví dụ: user nhập "12 23 34 45"
    text = update.message.text.strip()
    nums = [x for x in text.replace(',', ' ').split() if x.isdigit()]
    do_dai = context.user_data.get("do_dai_xien", 2)  # default 2, có thể lấy từ menu callback
    if len(nums) < do_dai:
        await update.message.reply_text(f"Cần ít nhất {do_dai} số để ghép xiên.")
        return
    results = tao_xien(nums, do_dai)
    if not results:
        await update.message.reply_text("Không tạo được bộ xiên.")
        return
    if len(results) > 20:
        # Nếu quá nhiều bộ, gửi chia nhóm
        text_result = '\n'.join([', '.join(results[i:i+10]) for i in range(0, len(results), 10)])
    else:
        text_result = ', '.join(results)
    await update.message.reply_text(f"{len(results)} bộ xiên {do_dai}:\n{text_result}")

# -- Handler nhận text để ghép càng 3D --
async def cang3d_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bước 1: Nhập số 2 chữ số (dãy)
    nums = context.user_data.get('cang3d_numbers', [])
    if not nums:
        text = update.message.text.strip()
        nums = [n for n in text.replace(',', ' ').split() if n.isdigit()]
        if not nums:
            await update.message.reply_text("Nhập các số 2 chữ số, cách nhau khoảng trắng.")
            return
        context.user_data['cang3d_numbers'] = nums
        await update.message.reply_text("Nhập các càng muốn ghép (ví dụ: 1 2 3):")
        return
    # Bước 2: Nhập càng
    text = update.message.text.strip()
    cangs = [c for c in text.replace(',', ' ').split() if c.isdigit()]
    if not cangs:
        await update.message.reply_text("Nhập các càng (chữ số).")
        return
    result = ghep_cang_3d(nums, cangs)
    await update.message.reply_text(f"Kết quả ghép càng 3D ({len(result)} số):\n" + ', '.join(result))
    context.user_data['cang3d_numbers'] = []  # reset

# -- Handler nhận text để ghép càng 4D --
async def cang4d_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nums = context.user_data.get('cang4d_numbers', [])
    if not nums:
        text = update.message.text.strip()
        nums = [n for n in text.replace(',', ' ').split() if n.isdigit() and len(n) == 3]
        if not nums:
            await update.message.reply_text("Nhập các số 3 chữ số, cách nhau khoảng trắng.")
            return
        context.user_data['cang4d_numbers'] = nums
        await update.message.reply_text("Nhập các càng muốn ghép (ví dụ: 1 2 3):")
        return
    text = update.message.text.strip()
    cangs = [c for c in text.replace(',', ' ').split() if c.isdigit()]
    if not cangs:
        await update.message.reply_text("Nhập các càng (chữ số).")
        return
    result = ghep_cang_4d(nums, cangs)
    await update.message.reply_text(f"Kết quả ghép càng 4D ({len(result)} số):\n" + ', '.join(result))
    context.user_data['cang4d_numbers'] = []

# -- Handler nhận text để đảo số --
async def daoso_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    s = ''.join([x for x in text if x.isdigit()])
    if len(s) < 2 or len(s) > 6:
        await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (vd 1234, 56789).")
        return
    results = dao_so(s)
    if not results:
        await update.message.reply_text("Không đảo được số.")
        return
    if len(results) > 20:
        text_result = '\n'.join([', '.join(results[i:i+10]) for i in range(0, len(results), 10)])
    else:
        text_result = ', '.join(results)
    await update.message.reply_text(f"Tổng {len(results)} hoán vị:\n{text_result}")

from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    # Ghép xiên
    if 'wait_for_xien_input' in user_data:
        do_dai = user_data['wait_for_xien_input']
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, do_dai)
        reply = f"{len(xiens)} bộ xiên {do_dai}:\n" + ', '.join(xiens[:50])
        await update.message.reply_text(reply)
        user_data.clear()
        return

    # Ghép càng 3D
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not all(len(n) == 2 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 2 chữ số!")
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    # Ghép càng 4D
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not all(len(n) == 3 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 3 chữ số!")
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    # Xử lý ghép càng sau khi có dãy & càng
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers" if kind == "3D" else "cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await update.message.reply_text("⚠️ Vui lòng nhập ít nhất 1 càng.")
            return
        result = [c + n for c in cangs for n in numbers]
        await update.message.reply_text(f"✅ Ghép {kind}: {len(result)} số\n" + ', '.join(result))
        user_data.clear()
        return

    # Nếu không có trạng thái nào
    return

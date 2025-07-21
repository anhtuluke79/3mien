from telegram import Update
from telegram.ext import ContextTypes

def extract_numbers(text):
    return [n for n in text.replace(',', ' ').split() if n.isdigit()]

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_data = context.user_data

    # ===== GHÉP XIÊN =====
    if isinstance(user_data.get('wait_for_xien_input'), int):
        numbers = extract_numbers(message.text)
        do_dai = user_data['wait_for_xien_input']
        from itertools import combinations
        xiens = ['&'.join(comb) for comb in combinations(numbers, do_dai)]

        reply = f"{len(xiens)} bộ xiên {do_dai}:
" + ', '.join(xiens) if xiens else "Không tạo được bộ xiên."
        await message.reply_text(reply)
        user_data.clear()
        return

    # ===== GHÉP CÀNG 3D =====
    if user_data.get('wait_for_cang3d_numbers'):
        arr = extract_numbers(message.text)
        if not arr:
            await message.reply_text("Vui lòng nhập dãy số (VD: 23 32 28 ...)")
            return
        user_data['cang3d_numbers'] = arr
        user_data['wait_for_cang3d_numbers'] = False
        user_data['wait_for_cang3d_cangs'] = True
        await message.reply_text("Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    if user_data.get('wait_for_cang3d_cangs'):
        cangs = extract_numbers(message.text)
        result = [c + n for c in cangs for n in user_data.get('cang3d_numbers', [])]
        await message.reply_text(f"Ghép càng 3D ({len(result)}):\n" + ', '.join(result))
        user_data.clear()
        return

    # ===== GHÉP CÀNG 4D =====
    if user_data.get('wait_for_cang4d_numbers'):
        arr = extract_numbers(message.text)
        if not arr or not all(len(n) == 3 for n in arr):
            await message.reply_text("Nhập các số 3 chữ số (VD: 123 456 ...)")
            return
        user_data['cang4d_numbers'] = arr
        user_data['wait_for_cang4d_numbers'] = False
        user_data['wait_for_cang4d_cangs'] = True
        await message.reply_text("Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    if user_data.get('wait_for_cang4d_cangs'):
        cangs = extract_numbers(message.text)
        result = [c + n for c in cangs for n in user_data.get('cang4d_numbers', [])]
        await message.reply_text(f"Ghép càng 4D ({len(result)}):\n" + ', '.join(result))
        user_data.clear()
        return

    # ===== ĐẢO SỐ =====
    if user_data.get('wait_for_daoso'):
        s = ''.join(extract_numbers(message.text))
        if not s.isdigit() or len(s) < 2 or len(s) > 6:
            await message.reply_text("Nhập 1 số từ 2 đến 6 chữ số để đảo hoán vị (VD: 1234)")
            return
        from itertools import permutations
        hoans = sorted(set([''.join(p) for p in permutations(s)]))
        await message.reply_text(f"Tổng {len(hoans)} hoán vị:\n" + ', '.join(hoans))
        user_data.clear()
        return

    # Nếu không phải đang chờ nhập, không phản hồi
    return

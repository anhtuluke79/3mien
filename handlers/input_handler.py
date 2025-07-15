from telegram.ext import ContextTypes
from utils.bot_functions import (
    split_numbers, ghep_xien, ghep_cang, chuan_hoa_can_chi,
    get_can_chi_ngay, sinh_so_hap_cho_ngay
)

async def all_text_handler(update, context: ContextTypes.DEFAULT_TYPE):
    # --- GHÉP XIÊN ---
    if context.user_data.get('wait_for_xien_input'):
        do_dai = context.user_data.get('do_dai')
        text = update.message.text.strip()
        numbers = split_numbers(text)
        if len(numbers) < do_dai:
            await update.message.reply_text(f"Bạn cần nhập ít nhất {do_dai} số!")
            return
        bo_xien = ghep_xien(numbers, do_dai)
        await update.message.reply_text(', '.join(bo_xien[:100]))
        context.user_data['wait_for_xien_input'] = False
        return

    # Ghép càng 3D
if context.user_data.get('wait_for_cang3d_numbers'):
    numbers = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 2]
    if not numbers:
        await update.message.reply_text("Vui lòng nhập các số 2 chữ số (cách nhau phẩy hoặc dấu cách, vd: 23 34 56).")
        return
    context.user_data['cang3d_numbers'] = numbers
    context.user_data['wait_for_cang3d_numbers'] = False
    context.user_data['wait_for_cang3d_cangs'] = True
    await update.message.reply_text("Nhập các càng (1 chữ số, cách nhau phẩy hoặc dấu cách, vd: 1 2 3):")
    return

if context.user_data.get('wait_for_cang3d_cangs'):
    cangs = [c for c in update.message.text.replace(',', ' ').split() if c.isdigit() and len(c) == 1]
    if not cangs:
        await update.message.reply_text("Vui lòng nhập các càng (1 chữ số, vd: 1 2 3):")
        return
    numbers = context.user_data.get('cang3d_numbers', [])
    result = []
    for c in cangs:
        for n in numbers:
            result.append(f"{c}{n}")
    await update.message.reply_text(','.join(result))
    context.user_data['wait_for_cang3d_cangs'] = False
    context.user_data['cang3d_numbers'] = []
    return

# Ghép càng 4D
if context.user_data.get('wait_for_cang4d_numbers'):
    numbers = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit() and len(n) == 3]
    if not numbers:
        await update.message.reply_text("Vui lòng nhập các số 3 chữ số (cách nhau phẩy hoặc dấu cách, vd: 123 234 456).")
        return
    context.user_data['cang4d_numbers'] = numbers
    context.user_data['wait_for_cang4d_numbers'] = False
    context.user_data['wait_for_cang4d_cangs'] = True
    await update.message.reply_text("Nhập các càng (1 chữ số, vd: 1 2 3):")
    return

if context.user_data.get('wait_for_cang4d_cangs'):
    cangs = [c for c in update.message.text.replace(',', ' ').split() if c.isdigit() and len(c) == 1]
    if not cangs:
        await update.message.reply_text("Vui lòng nhập các càng (1 chữ số, vd: 1 2 3):")
        return
    numbers = context.user_data.get('cang4d_numbers', [])
    result = []
    for c in cangs:
        for n in numbers:
            result.append(f"{c}{n}")
    await update.message.reply_text(','.join(result))
    context.user_data['wait_for_cang4d_cangs'] = False
    context.user_data['cang4d_numbers'] = []
    return

# ĐẢO SỐ
if context.user_data.get('wait_for_daoso'):
    # Hỗ trợ cả nhập 3 số, 4 số, hoặc nhiều số cách nhau phẩy/cách
    arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
    if not arr:
        await update.message.reply_text("Vui lòng nhập số (vd: 123, 1234 hoặc 23 45 67 ...).")
        return
    result = []
    from itertools import permutations
    for num in arr:
        if 2 <= len(num) <= 6:
            perm = set([''.join(p) for p in permutations(num)])
            result.append(','.join(sorted(perm)))
        else:
            result.append(num)
    await update.message.reply_text('\n'.join(result))
    context.user_data['wait_for_daoso'] = False
    return

    # --- PHONG THỦY NGÀY (nhập ngày dương) ---
    if context.user_data.get('wait_phongthuy_ngay') == 'duong':
        ngay = update.message.text.strip()
        if "-" in ngay and len(ngay.split('-')) == 3:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            ngay_str = f"{d:02d}/{m:02d}/{y}"
        else:
            await update.message.reply_text("Vui lòng nhập ngày đúng định dạng YYYY-MM-DD.")
            return
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
            return
        so_ghep = set(sohap_info['so_ghép'])
        text = (
            f"🔮 Phong thủy ngày {can_chi} {ngay_str}:\n"
            f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
            f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
            f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
            f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
        )
        await update.message.reply_text(text)
        context.user_data['wait_phongthuy_ngay'] = False
        return

    # --- PHONG THỦY NGÀY (nhập can chi) ---
    if context.user_data.get('wait_phongthuy_ngay') == 'canchi':
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
            return
        so_ghep = set(sohap_info['so_ghép'])
        text = (
            f"🔮 Phong thủy ngày {can_chi}:\n"
            f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
            f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
            f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
            f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
        )
        await update.message.reply_text(text)
        context.user_data['wait_phongthuy_ngay'] = False
        return

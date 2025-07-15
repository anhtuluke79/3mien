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

    # --- GHÉP CÀNG ---
    if context.user_data.get('wait_for_cang_input'):
        so_cang = context.user_data.get('so_cang')
        text = update.message.text.strip()
        numbers = split_numbers(text)
        if not numbers:
            await update.message.reply_text("Bạn cần nhập các số để ghép!")
            return
        bo_so = ghep_cang(numbers, so_cang)
        await update.message.reply_text(', '.join(bo_so[:100]))
        context.user_data['wait_for_cang_input'] = False
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

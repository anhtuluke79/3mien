from utils.bot_functions import split_numbers, ghep_xien, ghep_cang
from utils.phongthuy.phongthuy import chuan_hoa_can_chi, get_can_chi_ngay, sinh_so_hap_cho_ngay
from itertools import permutations

async def all_text_handler(update, context):
    # Ghép càng 3D - bước 1: nhập số
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

    # Ghép càng 3D - bước 2: nhập càng
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

    # Ghép càng 4D - bước 1: nhập số
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

    # Ghép càng 4D - bước 2: nhập càng
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

    # Đảo số (hàm hỗ trợ cả 3 số, 4 số, nhiều số)
    if context.user_data.get('wait_for_daoso'):
        arr = [n for n in update.message.text.replace(',', ' ').split() if n.isdigit()]
        if not arr:
            await update.message.reply_text("Vui lòng nhập số (vd: 123, 1234 hoặc 23 45 67 ...).")
            return
        result = []
        for num in arr:
            if 2 <= len(num) <= 6:
                perm = set([''.join(p) for p in permutations(num)])
                result.append(','.join(sorted(perm)))
            else:
                result.append(num)
        await update.message.reply_text('\n'.join(result))
        context.user_data['wait_for_daoso'] = False
        return

    if context.user_data.get('wait_for_feedback'):
        # Gửi góp ý về cho admin (tuỳ chỉnh theo ý bạn)
        ADMIN_ID = int(os.getenv("ADMIN_ID", "12345678"))
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✉️ Góp ý từ user @{update.effective_user.username}:\n{update.message.text}"
            )
        except Exception:
            pass
        await update.message.reply_text("🙏 Cảm ơn bạn đã đóng góp ý kiến! Bot sẽ tiếp nhận và phản hồi sớm nhất.")
        context.user_data['wait_for_feedback'] = False
        return
    # Ghép xiên
    if context.user_data.get('wait_for_xien_input'):
        do_dai = context.user_data.get('do_dai')
        text = update.message.text.strip()
        numbers = split_numbers(text)
        if len(numbers) < do_dai:
            await update.message.reply_text(f"Bạn cần nhập ít nhất {do_dai} số!")
            context.user_data['wait_for_xien_input'] = False
            return
        bo_xien = ghep_xien(numbers, do_dai)
        if not bo_xien:
            await update.message.reply_text("Không ghép được bộ xiên nào.")
        else:
            preview = ', '.join(bo_xien[:100])
            await update.message.reply_text(
                f"✅ {len(bo_xien)} bộ xiên {do_dai}:\n{preview}"
            )
        context.user_data['wait_for_xien_input'] = False
        return

    # Phong thủy ngày (dương)
    if context.user_data.get('wait_phongthuy_ngay') == 'duong':
        ngay = update.message.text.strip()
        try:
            y, m, d = map(int, ngay.split('-'))
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            if not sohap_info:
                await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
            else:
                so_ghep = set(sohap_info['so_ghép'])
                text = (
                    f"🔮 Phong thủy ngày {can_chi} ({d:02d}/{m:02d}/{y}):\n"
                    f"- Can: {sohap_info['can']}, {sohap_info['am_duong']}, {sohap_info['ngu_hanh']}\n"
                    f"- Số mệnh (ngũ hành): {sohap_info['so_menh']}\n"
                    f"- Số hạp của ngày: {', '.join(sohap_info['so_hap_list'])}\n"
                    f"- Bộ số ghép đặc biệt: {', '.join(so_ghep)}\n"
                )
                await update.message.reply_text(text)
        except Exception:
            await update.message.reply_text("Vui lòng nhập đúng định dạng YYYY-MM-DD.")
        context.user_data['wait_phongthuy_ngay'] = False
        return

    # Phong thủy ngày (can chi)
    if context.user_data.get('wait_phongthuy_ngay') == 'canchi':
        can_chi = chuan_hoa_can_chi(update.message.text.strip())
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        if not sohap_info:
            await update.message.reply_text(f"Không tra được số hạp cho ngày {can_chi}.")
        else:
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

    # Nếu không rơi vào bất cứ thao tác nào đang chờ, bot sẽ không phản hồi gì!
    return

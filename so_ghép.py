from itertools import combinations, permutations

# ===== GHÉP XIÊN =====
def ghep_xien(numbers, do_dai=2):
    """Ghép xiên (tổ hợp số theo độ dài)."""
    if len(numbers) < do_dai:
        return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

# ===== GHÉP CÀNG 3D =====
def ghep_cang3d(numbers, cang_list):
    """Ghép càng 3D: mỗi càng + từng số 2 chữ số."""
    result = []
    for c in cang_list:
        for n in numbers:
            result.append(c + n)
    return result

# ===== GHÉP CÀNG 4D =====
def ghep_cang4d(numbers, cang_list):
    """Ghép càng 4D: mỗi càng + từng số 3 chữ số."""
    result = []
    for c in cang_list:
        for n in numbers:
            result.append(c + n)
    return result

# ===== ĐẢO SỐ (hoán vị) =====
def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

# ===== HANDLER TEXT (Telegram) =====
async def so_ghep_text_handler(update, context):
    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    # ======= GHÉP XIÊN =======
    if mode == "xiens":
        do_dai = context.user_data.get("do_dai_xien", 2)
        arr = [n for n in text.replace(',', ' ').split() if n.isdigit()]
        bo_xien = ghep_xien(arr, do_dai)
        if not bo_xien:
            await update.message.reply_text("Không ghép được xiên.")
        else:
            if len(bo_xien) > 20:
                result = '\n'.join([', '.join(bo_xien[i:i+10]) for i in range(0, len(bo_xien), 10)])
            else:
                result = ', '.join(bo_xien)
            await update.message.reply_text(f"{len(bo_xien)} bộ xiên:\n{result}")
        context.user_data["mode"] = None
        return

    # ======= GHÉP CÀNG 3D =======
    if mode == "cang3d":
        if "wait_for_cang" not in context.user_data:
            arr = [n for n in text.replace(',', ' ').split() if n.isdigit() and len(n) == 2]
            if not arr:
                await update.message.reply_text("Nhập dãy số 2 chữ số (ví dụ: 23 32 28 ...)")
                return
            context.user_data['cang3d_numbers'] = arr
            context.user_data['wait_for_cang'] = True
            await update.message.reply_text("Nhập các càng muốn ghép (cách nhau phẩy hoặc dấu cách, ví dụ: 1 2 3):")
            return
        else:
            cang_list = [n for n in text.replace(',', ' ').split() if n.isdigit()]
            numbers = context.user_data.get('cang3d_numbers', [])
            result = ghep_cang3d(numbers, cang_list)
            await update.message.reply_text(f"Kết quả ghép càng 3D ({len(result)} số):\n" + ', '.join(result))
            context.user_data['wait_for_cang'] = False
            context.user_data['cang3d_numbers'] = []
            context.user_data["mode"] = None
            return

    # ======= GHÉP CÀNG 4D =======
    if mode == "cang4d":
        if "wait_for_cang" not in context.user_data:
            arr = [n for n in text.replace(',', ' ').split() if n.isdigit() and len(n) == 3]
            if not arr:
                await update.message.reply_text("Nhập dãy số 3 chữ số (ví dụ: 123 234 345 ...)")
                return
            context.user_data['cang4d_numbers'] = arr
            context.user_data['wait_for_cang'] = True
            await update.message.reply_text("Nhập các càng muốn ghép (cách nhau phẩy hoặc dấu cách, ví dụ: 1 2 3):")
            return
        else:
            cang_list = [n for n in text.replace(',', ' ').split() if n.isdigit()]
            numbers = context.user_data.get('cang4d_numbers', [])
            result = ghep_cang4d(numbers, cang_list)
            await update.message.reply_text(f"Kết quả ghép càng 4D ({len(result)} số):\n" + ', '.join(result))
            context.user_data['wait_for_cang'] = False
            context.user_data['cang4d_numbers'] = []
            context.user_data["mode"] = None
            return

    # ======= ĐẢO SỐ =======
    if mode == "daoso":
        s = text.replace(" ", "")
        if not s.isdigit() or not (2 <= len(s) <= 6):
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (ví dụ 1234, 56789).")
        else:
            result = dao_so(s)
            if len(result) > 20:
                result_text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                result_text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{result_text}")
        context.user_data["mode"] = None
        return

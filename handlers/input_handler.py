    from telegram import Update
    from telegram.ext import ContextTypes
    from handlers.xien import clean_numbers_input as clean_numbers_xien, gen_xien, format_xien_result
    from handlers.cang_dao import clean_numbers_input, ghep_cang, dao_so
    from handlers.kq import tra_ketqua_theo_ngay
    from handlers.phongthuy import phongthuy_tudong
    from handlers.keyboards import get_back_reset_keyboard
    from system.admin import log_user_action

    @log_user_action("Xử lý nhập tự do")
    async def handle_user_free_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
    return
    text = update.message.text.strip()
    user_data = context.user_data

    # ---- GHÉP XIÊN ----
    if user_data.get("wait_for_xien_input"):
    n = user_data.get("wait_for_xien_input")
    numbers = clean_numbers_xien(text)
    combos = gen_xien(numbers, n)
    result = format_xien_result(combos)
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    numbers = clean_numbers_input(text)
    user_data["cang3d_numbers"] = numbers
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
    user_data["wait_cang3d_cang"] = True
    user_data["wait_cang3d_numbers"] = None
    return

    if user_data.get("wait_cang3d_cang"):
    cang = text
    numbers = user_data.get("cang3d_numbers", [])
    result = ghep_cang(numbers, cang)
    msg = "Kết quả ghép càng 3D:\n" + ", ".join(result)
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    numbers = clean_numbers_input(text)
    user_data["cang4d_numbers"] = numbers
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
    user_data["wait_cang4d_cang"] = True
    user_data["wait_cang4d_numbers"] = None
    return

    if user_data.get("wait_cang4d_cang"):
    cang = text
    numbers = user_data.get("cang4d_numbers", [])
    result = ghep_cang(numbers, cang)
    msg = "Kết quả ghép càng 4D:\n" + ", ".join(result)
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    so = text
    result = dao_so(so)
    if result:
    msg = "Tất cả hoán vị:\n" + ", ".join(result)
    else:
    msg = "❗ Nhập số hợp lệ (2-6 chữ số)!"
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    ketqua = tra_ketqua_theo_ngay(text)
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )
    res = phongthuy_tudong(text)
    await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=result,
    parse_mode="Markdown",
    reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao")
    )

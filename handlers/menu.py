from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from utils.can_chi_utils import get_can_chi_ngay, sinh_so_hap_cho_ngay, phong_thuy_format, chot_so_format
from main import is_admin, main_menu_keyboard

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = main_menu_keyboard(user_id)
    await update.message.reply_text("🔹 Chọn chức năng:", reply_markup=keyboard)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Crawl XSMB", callback_data="admin_crawl_xsmb")],
        [InlineKeyboardButton("📥 Crawl XSMN", callback_data="admin_crawl_xsmn")],
        [InlineKeyboardButton("📥 Crawl XSMT", callback_data="admin_crawl_xsmt")],
        [InlineKeyboardButton("⬅️ Quay lại menu", callback_data="main_menu")],
    ]
    await update.callback_query.message.reply_text("⚙️ Quản trị:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "admin_menu":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu quản trị.")
            return
        await admin_menu(update, context)
        return

    if query.data == "phongthuy_ngay_today":
        now = datetime.now()
        can_chi = get_can_chi_ngay(now.year, now.month, now.day)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        today_str = now.strftime("%d/%m/%Y")
        text = phong_thuy_format(can_chi, sohap_info, is_today=True, today_str=today_str)
        await query.edit_message_text(text, parse_mode="Markdown")
        return

    if query.data == "chot_so_today":
        now = datetime.now()
        can_chi = get_can_chi_ngay(now.year, now.month, now.day)
        sohap_info = sinh_so_hap_cho_ngay(can_chi)
        today_str = now.strftime("%d/%m/%Y")
        text = chot_so_format(can_chi, sohap_info, today_str)
        await query.edit_message_text(text, parse_mode="Markdown")
        return

    # Quay lại menu chính
    if query.data == "main_menu":
        keyboard = main_menu_keyboard(user_id)
        await query.edit_message_text("🔹 Chọn chức năng:", reply_markup=keyboard)

import os
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from menu_handlers import menu, menu_callback_handler
from admin_handlers import admin_callback_handler
from user_manage import user_manage_callback_handler
from logic_xsmb import xsmb_text_handler
from so_ghép import so_ghep_text_handler
# KHÔNG import phongthuy_homnay_handler ở đây!

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ==== TEXT HANDLER ROUTER ====
async def all_text_handler(update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    user_id = update.effective_user.id
    logger.info(f"[all_text_handler] User {user_id} mode: {mode}")

    if mode == "xiens":
        await so_ghep_text_handler(update, context)
        return
    if mode == "cang3d":
        await so_ghep_text_handler(update, context)
        return
    if mode == "cang4d":
        await so_ghep_text_handler(update, context)
        return
    if mode == "daoso":
        await so_ghep_text_handler(update, context)
        return
    if mode == "phongthuy":
        from phongthuy import phongthuy_text_handler  # import tại đây để tránh lỗi vòng lặp
        await phongthuy_text_handler(update, context)
        return
    if mode == "xsmb" or mode == "thongke":
        await xsmb_text_handler(update, context)
        return

    # Nếu user chưa chọn chức năng nào thì hướng dẫn rõ ràng
    await update.message.reply_text(
        "Bạn chưa chọn chức năng. Hãy bấm /menu hoặc sử dụng menu dưới đây để bắt đầu."
    )
    logger.info(f"User {user_id} gửi tin nhắn ngoài chế độ nhập, đã được hướng dẫn.")

# ==== CALLBACK ROUTER ====
async def global_callback_handler(update, context):
    data = update.callback_query.data
    user_id = update.effective_user.id
    logger.info(f"[global_callback_handler] User {user_id} callback data: {data}")

    # Route theo prefix callback
    if data.startswith("admin_") or data.startswith("backup_") or data.startswith("restore_"):
        await admin_callback_handler(update, context)
        return
    if data.startswith("user_manage_"):
        await user_manage_callback_handler(update, context)
        return
    await menu_callback_handler(update, context)  # default: menu và các chức năng thường

# ==== HELP ====
async def help_handler(update, context):
    text = (
        "🤖 *Bot XSMB Phong thủy AI*\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start hoặc /menu - Mở menu chính\n"
        "/help - Xem hướng dẫn\n\n"
        "Bạn chọn chức năng bằng menu hoặc gõ số, càng, ...\n"
        "Nếu gặp lỗi hoặc cần hỗ trợ, liên hệ admin."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ==== ERROR LOG ====
async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)
    # Có thể báo lỗi cho admin ở đây nếu cần

# ==== MAIN ====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    app.add_error_handler(error_handler)
    logger.info("🤖 BOT XSMB đã chạy thành công!")
    app.run_polling()

if __name__ == "__main__":
    main()

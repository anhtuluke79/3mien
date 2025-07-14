from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from menu_handlers import (
    menu, menu_callback_handler, all_text_handler
)
from admin_handlers import (
    admin_menu, backup_restore_menu
)
from user_manage import (
    listusers, deluser, block_unapproved
)
from logic_xsmb import (
    thong_ke_xsmb, thong_ke_dau_duoi_db, predict_xsmb_rf
)
from phongthuy import (
    # các hàm phong thủy nếu cần
)
from config import logger

async def start_handler(update, context):
    await menu(update, context)

async def menu_handler(update, context):
    await menu(update, context)

async def help_handler(update, context):
    text = (
        "🤖 *Bot XSMB Phong thủy AI*\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start hoặc /menu - Mở menu chính\n"
        "/help - Xem hướng dẫn\n"
        "/listusers - Danh sách user đã duyệt (superadmin)\n"
        "/deluser <user_id> - Xóa quyền user\n"
        "\n"
        "Tính năng nổi bật:\n"
        "• Dự đoán AI XSMB\n"
        "• Ghép xiên, càng, đảo số\n"
        "• Tra cứu phong thủy ngày\n"
        "• Chốt số, nhiều chế độ\n"
        "• Thống kê, backup, quản trị, ủng hộ bot"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)
    # Có thể gửi lỗi về cho admin nếu cần

def register_handlers(app):
    # Command
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("listusers", listusers))
    app.add_handler(CommandHandler("deluser", deluser))
    # Callback/menu
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    # Text (xử lý nhập text cho các menu cần nhập)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, all_text_handler))
    # Block user chưa duyệt
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_unapproved))
    # Error handler
    app.add_error_handler(error_handler)

# handlers/menu.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    menu_keyboard = [
        [InlineKeyboardButton("💖 Ủng hộ & Góp ý", callback_data='support_feedback')],
        # thêm các nút khác nếu có
    ]
    return InlineKeyboardMarkup(menu_keyboard)


# handlers/text_handlers.py
from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler

def support_feedback_handler(update: Update, context: CallbackContext):
    caption = (
        "🌟 <b>Ủng hộ & Góp ý</b> 🌟\n\n"
        "Chân thành cảm ơn bạn đã quan tâm và sử dụng dịch vụ của chúng tôi. "
        "Nếu bạn thấy ứng dụng hữu ích và muốn góp phần hỗ trợ phát triển thêm những tính năng mới, bạn có thể ủng hộ qua tài khoản dưới đây:\n\n"
        "🏦 <b>Ngân hàng:</b> Vietcombank\n"
        "👤 <b>Chủ tài khoản:</b> Truong Anh Tu\n"
        "💳 <b>Số tài khoản:</b> 0071003914986\n\n"
        "Hoặc quét mã QR bên dưới để ủng hộ nhanh chóng và dễ dàng hơn!\n\n"
        "🙏 <b>Mọi đóng góp của bạn đều rất quý giá và sẽ giúp chúng tôi ngày càng hoàn thiện hơn.</b>\n\n"
        "Nếu bạn có bất kỳ góp ý nào, đừng ngần ngại gửi tin nhắn trực tiếp. "
        "Chúng tôi luôn lắng nghe và rất trân trọng những ý kiến đóng góp từ bạn.\n\n"
        "❤️ <b>Xin cảm ơn vì sự ủng hộ và đồng hành của bạn!</b>"
    )

    with open('qr_ung_ho.png', 'rb') as qr_image:
        update.callback_query.message.reply_photo(
            photo=qr_image,
            caption=caption,
            parse_mode='HTML'
        )

# main.py
from telegram.ext import Updater
from handlers.menu import get_main_menu
from handlers.text_handlers import support_feedback_handler

TOKEN = 'TOKEN_CUA_BAN'

def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(support_feedback_handler, pattern='support_feedback'))

    updater.start_polling()
    print("Bot đã chạy...")
    updater.idle()

if __name__ == '__main__':
    main()

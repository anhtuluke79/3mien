import logging
import os
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from itertools import combinations

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)

# --- Cấu hình Ban đầu ---
# Lấy token từ biến môi trường. Nếu không có, sẽ báo lỗi.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN chưa được thiết lập. Vui lòng thiết lập biến môi trường này.")

# Cấu hình logging để ghi lại các thông tin và lỗi của bot.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Cấu hình Scheduler cho các tác vụ định kỳ (ví dụ: gửi kết quả tự động) ---
scheduler = BackgroundScheduler()
scheduler.start()

# --- Định nghĩa các trạng thái cho ConversationHandler ---
# Các trạng thái cho luồng ghép càng
GH_CANG_TYPE, GH_CANG_LIST, GH_SO_LIST = range(3)
# Các trạng thái cho luồng ghép xiên
XIEN_SO_LIST, XIEN_KIEU = range(2)

# --- Hàm lấy kết quả xổ số miền Bắc ---
def get_kqxs_mienbac():
    """
    Lấy kết quả xổ số miền Bắc từ trang xsmn.mobi.
    Sử dụng BeautifulSoup để phân tích cú pháp HTML và trích xuất dữ liệu.
    Trả về một dictionary chứa các kết quả hoặc một dictionary báo lỗi.
    """
    url = "https://xsmn.mobi/xsmn-mien-bac"
    # Thiết lập User-Agent để tránh bị chặn bởi một số trang web
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Ném lỗi HTTP nếu phản hồi không thành công (ví dụ: 404, 500)
        
        soup = BeautifulSoup(response.text, "html.parser")
        # Tìm bảng kết quả dựa trên class
        table = soup.find("table", class_="bkqmienbac")
        if not table:
            logger.warning("Không tìm thấy bảng kết quả xổ số trên trang. Có thể cấu trúc HTML đã thay đổi.")
            return {"error": "Không tìm thấy bảng kết quả trên trang web. Vui lòng thử lại sau."}
        
        results = {}
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True) # Nhãn của giải (ví dụ: "Giải Đặc Biệt")
                # Nối tất cả các cột còn lại làm số kết quả
                numbers = ' '.join(col.get_text(strip=True) for col in cols[1:])
                results[label] = numbers
        logger.info("Đã lấy kết quả xổ số miền Bắc thành công.")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi yêu cầu kết quả xổ số: {e}")
        return {"error": f"Lỗi kết nối hoặc yêu cầu tới trang web: {e}. Vui lòng kiểm tra kết nối internet hoặc thử lại sau."}
    except Exception as e:
        logger.error(f"Lỗi không xác định khi lấy kết quả xổ số: {e}")
        return {"error": f"Đã xảy ra lỗi không mong muốn khi lấy kết quả: {e}. Vui lòng thử lại."}

# --- Hàm tải ảnh kết quả xổ số ---
def download_lottery_image():
    """
    Tải ảnh kết quả xổ số từ minhchinh.com và lưu vào file cục bộ.
    Trả về đường dẫn file ảnh nếu tải thành công, None nếu thất bại.
    """
    try:
        url = "https://www.minhchinh.com/images/kqxsmb.jpg"
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Ném lỗi HTTP nếu phản hồi không thành công
        
        image_path = "latest_kqxs.jpg"
        with open(image_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Đã tải ảnh kết quả xổ số thành công về {image_path}")
        return image_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi tải ảnh kết quả xổ số từ URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải ảnh: {e}")
        return None

# --- Hàm gửi ảnh kết quả xổ số (được gọi bởi scheduler) ---
async def send_lottery_image(context: CallbackContext):
    """
    Gửi ảnh kết quả xổ số đã tải về cho người dùng thông qua bot.
    Chức năng này được gọi bởi BackgroundScheduler.
    """
    chat_id = context.job.data.get("chat_id")
    logger.info(f"Đang cố gắng gửi ảnh kết quả xổ số cho chat ID: {chat_id}")
    
    image_path = download_lottery_image()
    
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img:
                await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📸 📊 Xem kết quả xổ số hôm nay")
            logger.info(f"Đã gửi ảnh kết quả xổ số thành công cho chat ID: {chat_id}")
            # Xóa ảnh sau khi gửi để tiết kiệm dung lượng
            os.remove(image_path)
            logger.info(f"Đã xóa ảnh {image_path} sau khi gửi.")
        except Exception as e:
            logger.error(f"Lỗi khi gửi ảnh cho chat ID {chat_id}: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ Lỗi khi gửi ảnh kết quả hôm nay.")
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ Không tìm thấy ảnh kết quả hôm nay hoặc lỗi khi tải ảnh. Vui lòng thử lại sau.")

# --- Các hàm xử lý lệnh và callback ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý lệnh /start.
    Gửi lời chào mừng và hướng dẫn người dùng sử dụng lệnh /menu.
    """
    await update.message.reply_text("✨ Chào mừng bạn đến với bot Xổ Số Telegram! Sử dụng lệnh /menu để bắt đầu.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Hiển thị menu chính của bot với các tùy chọn chức năng.
    Sử dụng InlineKeyboard để tạo các nút bấm tương tác.
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 Xem kết quả", callback_data="kqxs"),
            InlineKeyboardButton("🧠 Gợi ý số bằng AI", callback_data="goi_y_so_ai")
        ],
        [
            InlineKeyboardButton("🎯 Ghép số (Càng / Xiên)", callback_data="chon_ghep")
        ],
        [
            InlineKeyboardButton("🕒 Tự động gửi kết quả", callback_data="bat_tudong")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Kiểm tra nếu là callback query (người dùng bấm nút) thì sửa tin nhắn hiện tại,
    # nếu không (người dùng gõ /menu) thì gửi tin nhắn mới.
    if update.callback_query:
        await update.callback_query.edit_message_text("📋 Vui lòng chọn chức năng bên dưới:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("📋 Vui lòng chọn chức năng bên dưới:", reply_markup=reply_markup)

async def kqxs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý yêu cầu xem kết quả xổ số.
    Gọi hàm get_kqxs_mienbac để lấy dữ liệu và hiển thị cho người dùng.
    """
    # Lấy đối tượng tin nhắn hoặc callback query để phản hồi
    target_message = update.callback_query or update.message

    if not target_message:
        logger.error("Không có đối tượng tin nhắn hoặc callback query để phản hồi trong kqxs_handler.")
        return

    await target_message.reply_text("⏳ Đang lấy kết quả xổ số, vui lòng đợi...")
    result = get_kqxs_mienbac()

    if "error" in result:
        await target_message.reply_text(f"❌ Lỗi khi lấy kết quả: {result['error']}")
        return
    
    reply = "📊 *Kết quả xổ số miền Bắc hôm nay:*\n\n"
    for label, val in result.items():
        reply += f"*{label}*: `{val}`\n" # Sử dụng Markdown để định dạng
    
    await target_message.reply_text(reply, parse_mode='Markdown')
    
    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await target_message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Luồng xử lý ghép càng ---
async def ghepcang_popup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bắt đầu luồng ghép càng.
    Khởi tạo dữ liệu người dùng trong context.user_data và yêu cầu loại càng.
    """
    # Sử dụng context.user_data để lưu trữ dữ liệu tạm thời cho người dùng hiện tại
    context.user_data['gh_cang'] = {} 
    
    # Lấy đối tượng tin nhắn hoặc callback query để phản hồi
    target_message = update.callback_query or update.message

    if not target_message:
        logger.error("Không có đối tượng tin nhắn hoặc callback query để phản hồi trong ghepcang_popup.")
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.edit_message_text("🔢 Vui lòng nhập loại ghép càng (3D hoặc 4D):")
    else:
        await update.message.reply_text("🔢 Vui lòng nhập loại ghép càng (3D hoặc 4D):", reply_markup=ReplyKeyboardRemove())
    
    return GH_CANG_TYPE

async def ghepcang_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Nhận loại càng (3D/4D) từ người dùng.
    Kiểm tra tính hợp lệ và yêu cầu danh sách số càng.
    """
    kieu = update.message.text.strip().upper()
    if kieu not in ["3D", "4D"]:
        await update.message.reply_text("⚠️ Chỉ chấp nhận '3D' hoặc '4D'. Vui lòng nhập lại:")
        return GH_CANG_TYPE
    
    context.user_data['gh_cang']["kieu"] = kieu
    await update.message.reply_text("✏️ Vui lòng nhập danh sách số càng, cách nhau bởi dấu cách (VD: `3 4`):", parse_mode='Markdown')
    return GH_CANG_LIST

async def ghepcang_cang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Nhận danh sách số càng từ người dùng.
    Kiểm tra tính hợp lệ và yêu cầu các số để ghép.
    """
    cangs_raw = update.message.text.strip().split()
    # Lọc chỉ lấy các phần tử là số
    cangs = [c for c in cangs_raw if c.isdigit()]

    if not cangs:
        await update.message.reply_text("⚠️ Bạn chưa nhập càng hoặc càng không hợp lệ. Vui lòng nhập lại các chữ số càng (VD: `3 4`):", parse_mode='Markdown')
        return GH_CANG_LIST
    
    context.user_data['gh_cang']["cangs"] = cangs
    await update.message.reply_text("✏️ Vui lòng nhập các số để ghép, cách nhau bởi dấu cách (VD: `123 456`):", parse_mode='Markdown')
    return GH_SO_LIST

async def ghepcang_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Thực hiện ghép càng dựa trên dữ liệu đã nhập.
    Hiển thị kết quả và kết thúc ConversationHandler.
    """
    # Lọc chỉ lấy các số và đệm thành 3 chữ số nếu cần (ví dụ: "12" thành "012")
    numbers_raw = update.message.text.strip().split()
    numbers = [x.zfill(3) for x in numbers_raw if x.isdigit()]

    data = context.user_data.get('gh_cang', {})
    
    if not numbers or "kieu" not in data or "cangs" not in data:
        await update.message.reply_text("❌ Dữ liệu bị thiếu hoặc không hợp lệ. Vui lòng gõ /menu để bắt đầu lại.")
        context.user_data.pop('gh_cang', None) # Xóa dữ liệu cũ
        return ConversationHandler.END

    results = []
    kieu = data["kieu"]
    for cang in data["cangs"]:
        for num in numbers:
            if kieu == "3D":
                # Ghép càng với 2 số cuối của số (ví dụ: càng '3', số '123' -> '323')
                results.append(f"{cang}{num[-2:]}")
            elif kieu == "4D":
                # Ghép càng với toàn bộ số (đã được đệm 3 chữ số, ví dụ: càng '1', số '123' -> '1123')
                results.append(f"{cang}{num}")

    if not results:
        await update.message.reply_text("❌ Không có kết quả nào phù hợp với các số bạn đã nhập.")
    else:
        await update.message.reply_text(f"✨ *Kết quả ghép càng {kieu}:*\n`{'`, `'.join(results)}`", parse_mode='Markdown')
        keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
        await update.message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data.pop('gh_cang', None) # Xóa dữ liệu sau khi hoàn thành
    return ConversationHandler.END

# --- Luồng xử lý ghép xiên ---
async def ghepxien_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bắt đầu luồng ghép xiên.
    Khởi tạo dữ liệu người dùng trong context.user_data và yêu cầu danh sách số.
    """
    context.user_data['xien_data'] = {}
    
    # Lấy đối tượng tin nhắn hoặc callback query để phản hồi
    target_message = update.callback_query or update.message

    if not target_message:
        logger.error("Không có đối tượng tin nhắn hoặc callback query để phản hồi trong ghepxien_start.")
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.edit_message_text("🔢 Vui lòng nhập các số muốn ghép xiên, cách nhau bởi dấu cách (VD: `22 33 44`):", parse_mode='Markdown')
    else:
        await update.message.reply_text("🔢 Vui lòng nhập các số muốn ghép xiên, cách nhau bởi dấu cách (VD: `22 33 44`):", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    
    return XIEN_SO_LIST

async def ghepxien_sos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Nhận danh sách số để ghép xiên từ người dùng.
    Kiểm tra tính hợp lệ và yêu cầu kiểu xiên.
    """
    numbers_raw = update.message.text.strip().split()
    numbers = [n for n in numbers_raw if n.isdigit()] # Chỉ lấy các phần tử là số

    if len(numbers) < 2:
        await update.message.reply_text("⚠️ Bạn cần nhập ít nhất 2 số và chúng phải là số. Vui lòng nhập lại:")
        return XIEN_SO_LIST
    
    context.user_data['xien_data']["numbers"] = numbers
    await update.message.reply_text("🔢 Vui lòng nhập kiểu xiên (2, 3 hoặc 4):")
    return XIEN_KIEU

async def ghepxien_kieu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Thực hiện ghép xiên dựa trên dữ liệu đã nhập.
    Hiển thị kết quả và kết thúc ConversationHandler.
    """
    data = context.user_data.get('xien_data', {})
    numbers = data.get("numbers", [])

    try:
        kieu = int(update.message.text.strip())
        # Kiểm tra kiểu xiên phải từ 2 đến 4 và không lớn hơn số lượng số đã nhập
        if not (2 <= kieu <= 4 and kieu <= len(numbers)):
            raise ValueError
    except ValueError:
        await update.message.reply_text(f"⚠️ Kiểu xiên không hợp lệ. Vui lòng nhập số 2, 3 hoặc 4, và không lớn hơn số lượng số bạn đã nhập ({len(numbers)}):")
        return XIEN_KIEU

    # Tạo các tổ hợp (combinations) của các số
    result = [ '&'.join(combo) for combo in combinations(numbers, kieu) ]
    result_text = ', '.join(result)
    await update.message.reply_text(f"✨ *Kết quả ghép xiên {kieu}:*\n`{result_text}`", parse_mode='Markdown')

    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("👉 Bạn muốn làm gì tiếp?", reply_markup=InlineKeyboardMarkup(keyboard))

    context.user_data.pop('xien_data', None) # Xóa dữ liệu sau khi hoàn thành
    return ConversationHandler.END

# --- Hàm bật tự động gửi kết quả ---
async def bat_tudong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Đặt lịch tự động gửi ảnh kết quả xổ số hàng ngày vào lúc 18:40.
    """
    chat_id = update.effective_chat.id
    job_id = f'xsmb_auto_send_{chat_id}' # ID duy nhất cho job của từng chat
    
    # Lấy đối tượng tin nhắn hoặc callback query để phản hồi
    target_message = update.callback_query or update.message

    if not target_message:
        logger.error("Không có đối tượng tin nhắn hoặc callback query để phản hồi trong bat_tudong.")
        return

    # Kiểm tra xem job đã tồn tại chưa để tránh thêm trùng lặp
    if scheduler.get_job(job_id):
        await target_message.reply_text("✅ Chức năng tự động gửi kết quả đã được bật trước đó cho cuộc trò chuyện này.")
        logger.info(f"Job tự động gửi kết quả cho chat ID {chat_id} đã tồn tại.")
    else:
        scheduler.add_job(
            send_lottery_image,
            trigger='cron',
            hour=18, minute=40, # Đặt giờ và phút cụ thể
            kwargs={"context": context, "chat_id": chat_id},
            id=job_id,
            replace_existing=True # Đảm bảo chỉ có một job với ID này
        )
        await target_message.reply_text("✅ Đã bật gửi ảnh kết quả xổ số vào lúc *18:40* mỗi ngày.", parse_mode='Markdown')
        logger.info(f"Đã lên lịch job tự động gửi kết quả cho chat ID: {chat_id}")

# --- Hàm hủy bỏ thao tác hiện tại ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Hủy bỏ ConversationHandler hiện tại.
    Xóa dữ liệu tạm thời của người dùng và hiển thị menu chính.
    """
    # Xóa dữ liệu tạm thời của người dùng nếu có
    context.user_data.pop('gh_cang', None)
    context.user_data.pop('xien_data', None)
    
    await update.message.reply_text("⛔️ Đã hủy bỏ thao tác hiện tại.", reply_markup=ReplyKeyboardRemove())
    
    keyboard = [[InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]]
    await update.message.reply_text("👉 Bạn muốn làm gì tiếp?:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    return ConversationHandler.END

# --- Hàm xử lý các callback query từ menu chính ---
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý các callback query được gửi từ các nút InlineKeyboard trong menu chính.
    Chuyển hướng đến các hàm xử lý tương ứng dựa trên `callback_data`.
    """
    query = update.callback_query
    await query.answer() # Luôn gọi query.answer() để loại bỏ trạng thái loading trên nút bấm

    cmd = query.data

    if cmd == "kqxs":
        await kqxs_handler(update, context)
    elif cmd == "ghepcang":
        # Chuyển hướng đến entry point của ConversationHandler cho ghép càng
        await ghepcang_popup(update, context)
    elif cmd == "ghepxien":
        # Chuyển hướng đến entry point của ConversationHandler cho ghép xiên
        await ghepxien_start(update, context)
    elif cmd == "bat_tudong":
        await bat_tudong(update, context)
    elif cmd == "chon_ghep":
        # Hiển thị menu phụ cho chức năng ghép số
        keyboard = [
            [InlineKeyboardButton("🎯 Bắt đầu Ghép Càng", callback_data="ghepcang")],
            [InlineKeyboardButton("➕ Bắt đầu Ghép Xiên", callback_data="ghepxien")],
            [InlineKeyboardButton("⬅️ Trở về menu chính", callback_data="back_to_menu")]
        ]
        await query.edit_message_text("🔧 Vui lòng chọn tính năng ghép số:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif cmd == "goi_y_so_ai":
        await query.edit_message_text("🧠 Tính năng *Gợi ý số bằng AI* đang được phát triển. Vui lòng quay lại sau!", parse_mode='Markdown')
    elif cmd == "back_to_menu":
        await menu(update, context)
    else:
        await query.edit_message_text("❌ Lựa chọn không hợp lệ, vui lòng thử lại.")

# --- Hàm Main để khởi chạy Bot ---
def main():
    """
    Hàm chính để khởi tạo và chạy Telegram bot.
    Đăng ký tất cả các handler (lệnh, callback, hội thoại).
    """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # --- Đăng ký các CommandHandler (lệnh bắt đầu bằng '/') ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bat_tudong", bat_tudong))
    app.add_handler(CommandHandler("cancel", cancel)) # Lệnh hủy bỏ ConversationHandler

    # --- Đăng ký CallbackQueryHandler cho các nút bấm trong menu chính ---
    app.add_handler(CallbackQueryHandler(handle_menu_callback))

    # --- Đăng ký ConversationHandler cho Ghép Càng ---
    # entry_points: Điểm bắt đầu của cuộc hội thoại (khi người dùng bấm nút "ghepcang")
    # states: Các trạng thái và handler tương ứng cho mỗi trạng thái
    # fallbacks: Các handler được gọi nếu cuộc hội thoại không khớp với trạng thái hiện tại (ví dụ: gõ /cancel)
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepcang_popup, pattern="^ghepcang$")],
        states={
            GH_CANG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_type)],
            GH_CANG_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_cang)],
            GH_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepcang_so)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True # Cho phép người dùng bắt đầu lại cuộc hội thoại nếu đang ở giữa
    ))

    # --- Đăng ký ConversationHandler cho Ghép Xiên ---
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ghepxien_start, pattern="^ghepxien$")],
        states={
            XIEN_SO_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_sos)],
            XIEN_KIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, ghepxien_kieu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True # Cho phép người dùng bắt đầu lại cuộc hội thoại nếu đang ở giữa
    ))

    logger.info("🚀 Bot Telegram đang chạy và sẵn sàng nhận lệnh...")
    app.run_polling() # Bắt đầu polling để nhận các update từ Telegram API

if __name__ == "__main__":
    main()



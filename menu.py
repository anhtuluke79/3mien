from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    keyboard = [
        [
            InlineKeyboardButton("📈 Thống kê", callback_data="thongke"),
            InlineKeyboardButton("🧠 Dự đoán AI", callback_data="du_doan_ai"),
            InlineKeyboardButton("🔮 Phong thủy ngày", callback_data="phongthuy_ngay"),
        ],
        [
            InlineKeyboardButton("➕ Ghép xiên", callback_data="ghepxien"),
            InlineKeyboardButton("🎯 Ghép càng", callback_data="ghepcang"),
            # ĐÃ BỎ nút "💬 Hỏi Thần tài"
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton("⚙️ Train lại AI", callback_data="train_model"),
            InlineKeyboardButton("🛠️ Cập nhật XSMB", callback_data="capnhat_xsmb"),
        ])
    text = "🔹 Chọn chức năng:"
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard)
        )

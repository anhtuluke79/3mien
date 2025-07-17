from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.phongthuy.phongthuy import get_can_chi_ngay
from utils.bot_functions import (
    split_numbers, ghep_xien, ghep_cang, chuan_hoa_can_chi,
    get_can_chi_ngay, sinh_so_hap_cho_ngay
)
from handlers.menu import ungho_menu_handler, ungho_ck_handler, donggop_ykien_handler
from utils.crawl_xsmb import crawl_xsmb_Nngay_minhchinh_csv
from utils.bot_functions import predict_rf_xsmb, predict_rf_lo_mb
import os

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "12345678").split(',')))

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # --- GHÉP XIÊN ---
    if query.data == "ghepxien":
        keyboard = [
            [
                InlineKeyboardButton("🟢 Xiên 2", callback_data="ghepxien_2"),
                InlineKeyboardButton("🟦 Xiên 3", callback_data="ghepxien_3"),
                InlineKeyboardButton("🟣 Xiên 4", callback_data="ghepxien_4"),
            ],
            [
                InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu"),
            ]
        ]
        await query.edit_message_text(
            "<b>Chọn dạng ghép xiên:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data.startswith("ghepxien_"):
        do_dai = int(query.data.split("_")[1])
        context.user_data['do_dai'] = do_dai
        context.user_data['wait_for_xien_input'] = True
        await query.edit_message_text(
            f"🔢 <b>Nhập dãy số (cách nhau bởi dấu cách hoặc phẩy) để ghép xiên {do_dai}:</b>\n"
            "<i>VD: 23 33 44 55 66</i>",
            parse_mode="HTML"
        )

    # --- GHÉP CÀNG ---
    elif query.data == "ghepcang":
        keyboard = [
            [
                InlineKeyboardButton("🟢 Ghép càng 3D", callback_data="ghepcang_3d"),
                InlineKeyboardButton("🟦 Ghép càng 4D", callback_data="ghepcang_4d"),
            ],
            [
                InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu"),
            ]
        ]
        await query.edit_message_text(
            "🎯 <b>Bạn muốn ghép càng kiểu nào?</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data == "ghepcang_3d":
        context.user_data.clear()
        context.user_data['wait_for_cang3d_numbers'] = True
        await query.edit_message_text(
            "🔢 <b>Nhập các số 2 chữ số để ghép (cách nhau bởi dấu cách hoặc phẩy):</b>\n<i>VD: 23 34 56</i>",
            parse_mode="HTML"
        )

    elif query.data == "ghepcang_4d":
        context.user_data.clear()
        context.user_data['wait_for_cang4d_numbers'] = True
        await query.edit_message_text(
            "🔢 <b>Nhập các số 3 chữ số để ghép (cách nhau bởi dấu cách hoặc phẩy):</b>\n<i>VD: 123 234 456</i>",
            parse_mode="HTML"
        )

    elif query.data == "daoso":
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text(
            "🔁 <b>Nhập số cần đảo:</b>\n"
            "<i>VD: 123, 1234 hoặc nhiều số cách nhau dấu cách</i>",
            parse_mode="HTML"
        )

    # --- PHONG THỦY NGÀY ---
    elif query.data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("📅 Nhập ngày dương (YYYY-MM-DD)", callback_data="ptn_ngay_duong")],
            [InlineKeyboardButton("📜 Nhập can chi (VD: Giáp Tý)", callback_data="ptn_can_chi")],
            [InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "<b>Bạn muốn tra phong thủy theo kiểu nào?</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data == "ptn_ngay_duong":
        await query.edit_message_text(
            "📅 <b>Nhập ngày dương lịch (YYYY-MM-DD):</b>",
            parse_mode="HTML"
        )
        context.user_data['wait_phongthuy_ngay'] = 'duong'

    elif query.data == "ptn_can_chi":
        await query.edit_message_text(
            "📜 <b>Nhập can chi (VD: Giáp Tý):</b>",
            parse_mode="HTML"
        )
        context.user_data['wait_phongthuy_ngay'] = 'canchi'

    # --- AI MENU ---
    elif query.data == "ai_menu":
        keyboard = [
            [InlineKeyboardButton("🎯 Dự đoán giải ĐB", callback_data="ai_rf_db")],
            [InlineKeyboardButton("🔢 Dự đoán lô MB", callback_data="ai_rf_lo")],
            [InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "<b>Chọn chức năng dự đoán AI Random Forest:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data == "ai_rf_db":
        try:
            kq = predict_rf_xsmb("xsmb.csv", "model_rf_xsmb.pkl", 7)
            await query.edit_message_text(
                f"🎯 <b>Dự đoán AI RF giải ĐB miền Bắc:</b> <code>{kq}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Lỗi dự đoán AI: {e}")

    elif query.data == "ai_rf_lo":
        try:
            kq = predict_rf_lo_mb("xsmb.csv", "model_rf_lo_mb.pkl", 7)
            await query.edit_message_text(
                f"🔢 <b>Dự đoán AI RF lô miền Bắc:</b> <code>{kq}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Lỗi dự đoán AI: {e}")

    # --- ỦNG HỘ / ĐÓNG GÓP ---
    elif query.data == "ungho_menu":
        await ungho_menu_handler(update, context)
    elif query.data == "ungho_ck":
        await ungho_ck_handler(update, context)
    elif query.data == "donggop_ykien":
        await donggop_ykien_handler(update, context)

    # --- ADMIN CHỨC NĂNG ---
    elif query.data == "admin_menu":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Bạn không có quyền truy cập menu admin!")
            return
        keyboard = [
            [InlineKeyboardButton("⚙️ Train lại AI RF ĐB", callback_data="train_model_db")],
            [InlineKeyboardButton("⚙️ Train lại AI RF Lô", callback_data="train_model_lo")],
            [InlineKeyboardButton("🔄 Cập nhật XSMB", callback_data="capnhat_xsmb")],
            [InlineKeyboardButton("🏠 Quay lại menu", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "<b>🛠️ Menu quản trị bot</b>\nChọn chức năng dành cho admin:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Bạn không có quyền cập nhật dữ liệu!")
            return
        try:
            await query.edit_message_text("🔄 Đang cập nhật XSMB, chỉ thêm ngày mới...")
            df = crawl_xsmb_Nngay_minhchinh_csv(60, "xsmb.csv")
            if df is not None:
                await query.message.reply_text(
                    f"✅ Đã cập nhật file xsmb.csv ({len(df)} ngày dữ liệu, không trùng lặp ngày)."
                )
            else:
                await query.message.reply_text(
                    "❌ Không có dữ liệu mới nào để cập nhật."
                )
        except Exception as e:
            await query.message.reply_text(f"❌ Lỗi cập nhật: {e}")

    # --- QUAY LẠI MENU ---
    elif query.data == "main_menu":
        from handlers.menu import menu
        await menu(update, context)

    else:
        await query.edit_message_text("⏳ Chức năng đang phát triển.")

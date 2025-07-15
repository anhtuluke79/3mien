from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.bot_functions import (
    split_numbers, ghep_xien, ghep_cang, chuan_hoa_can_chi,
    get_can_chi_ngay, sinh_so_hap_cho_ngay, crawl_lich_su_xsmb
)
import pandas as pd
import joblib
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
                InlineKeyboardButton("Xiên 2", callback_data="ghepxien_2"),
                InlineKeyboardButton("Xiên 3", callback_data="ghepxien_3"),
                InlineKeyboardButton("Xiên 4", callback_data="ghepxien_4"),
            ]
        ]
        await query.edit_message_text("Chọn dạng ghép xiên:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("ghepxien_"):
        do_dai = int(query.data.split("_")[1])
        context.user_data['do_dai'] = do_dai
        context.user_data['wait_for_xien_input'] = True
        await query.edit_message_text(
            f"Nhập dãy số (cách nhau bởi dấu cách hoặc phẩy) để ghép xiên {do_dai}:"
        )

    # --- GHÉP CÀNG ---
    elif query.data == "ghepcang":
        keyboard = [
            [
                InlineKeyboardButton("Ghép càng 3D", callback_data="ghepcang_3d"),
                InlineKeyboardButton("Ghép càng 4D", callback_data="ghepcang_4d"),
            ],
            [
                InlineKeyboardButton("Đảo số", callback_data="daoso"),
            ]
        ]
        await query.edit_message_text("Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ghepcang_3d":
        context.user_data.clear()
        context.user_data['wait_for_cang3d_numbers'] = True
        await query.edit_message_text("Nhập các số 2 chữ số để ghép (cách nhau bởi dấu cách hoặc phẩy):")

    elif query.data == "ghepcang_4d":
        context.user_data.clear()
        context.user_data['wait_for_cang4d_numbers'] = True
        await query.edit_message_text("Nhập các số 3 chữ số để ghép (cách nhau bởi dấu cách hoặc phẩy):")

    elif query.data == "daoso":
        context.user_data.clear()
        context.user_data['wait_for_daoso'] = True
        await query.edit_message_text("Nhập số cần đảo (vd: 123, 1234, hoặc nhiều số cách nhau dấu cách):")

    # --- THỐNG KÊ XỔ SỐ ---
    elif query.data == "thongke":
        try:
            df = pd.read_csv('xsmb.csv')
            dbs = df['ĐB'].astype(str).str[-2:]
            counts = dbs.value_counts().head(10)
            top_list = "\n".join([f"Số {i}: {v} lần" for i, v in counts.items()])
            today_db = dbs.iloc[0] if len(dbs) > 0 else "?"
            text = (
                f"📈 Top 10 số ĐB xuất hiện nhiều nhất 30 ngày gần nhất:\n{top_list}\n"
                f"\n🎯 Số ĐB hôm nay: {today_db}"
            )
            await query.edit_message_text(text)
        except Exception as e:
            await query.edit_message_text(f"Lỗi thống kê: {e}")

    # --- PHONG THỦY NGÀY ---
    elif query.data == "phongthuy_ngay":
        keyboard = [
            [InlineKeyboardButton("Nhập ngày dương (YYYY-MM-DD)", callback_data="ptn_ngay_duong")],
            [InlineKeyboardButton("Nhập can chi (ví dụ: Giáp Tý)", callback_data="ptn_can_chi")]
        ]
        await query.edit_message_text("Bạn muốn tra phong thủy theo kiểu nào?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "ptn_ngay_duong":
        await query.edit_message_text("Nhập ngày dương lịch (YYYY-MM-DD):")
        context.user_data['wait_phongthuy_ngay'] = 'duong'

    elif query.data == "ptn_can_chi":
        await query.edit_message_text("Nhập can chi (ví dụ: Giáp Tý):")
        context.user_data['wait_phongthuy_ngay'] = 'canchi'

    # --- DỰ ĐOÁN AI ---
    elif query.data == "du_doan_ai":
        try:
            df = pd.read_csv('xsmb.csv')
            df = df.dropna()
            dbs = df['ĐB'].astype(str).str[-2:].astype(int)
            if not os.path.exists('model_rf_loto.pkl'):
                await query.edit_message_text("Chưa có mô hình AI, cần train trước bằng nút Train lại AI.")
                return
            model = joblib.load('model_rf_loto.pkl')
            last7 = dbs[:7].tolist()
            if len(last7) < 7:
                await query.edit_message_text("Không đủ dữ liệu 7 ngày để dự đoán!")
                return
            probs = model.predict_proba([last7])[0]
            top_idx = probs.argsort()[-3:][::-1]
            ketqua = [f"{model.classes_[i]:02d}" for i in top_idx]
            await query.edit_message_text(
                "🤖 Dự đoán AI (RandomForest) cho lần quay tiếp theo:\n"
                f"Top 3 số: {', '.join(ketqua)}"
            )
        except Exception as e:
            await query.edit_message_text(f"Lỗi dự đoán AI: {e}")

    # --- TRAIN MODEL (ADMIN) ---
    elif query.data == "train_model":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền train lại mô hình!")
            return
        try:
            await query.edit_message_text("⏳ Đang train lại AI, vui lòng đợi...")
            df = pd.read_csv('xsmb.csv')
            df = df.dropna()
            dbs = df['ĐB'].astype(str).str[-2:].astype(int)
            X, y = [], []
            for i in range(len(dbs) - 7):
                features = dbs[i:i+7].tolist()
                label = dbs[i+7]
                X.append(features)
                y.append(label)
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            joblib.dump(model, 'model_rf_loto.pkl')
            await query.edit_message_text("✅ Đã train lại và lưu mô hình thành công!")
        except Exception as e:
            await query.edit_message_text(f"Lỗi khi train mô hình: {e}")

    # --- CẬP NHẬT XSMB (ADMIN) ---
    elif query.data == "capnhat_xsmb":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("Bạn không có quyền cập nhật dữ liệu!")
            return
        try:
            ok = crawl_lich_su_xsmb("xsmb.csv")
            if ok:
                await query.edit_message_text("✅ Đã cập nhật dữ liệu xsmb.csv thành công (từ xsmn.mobi)!")
            else:
                await query.edit_message_text("❌ Không lấy được dữ liệu mới, vui lòng thử lại sau.")
        except Exception as e:
            await query.edit_message_text(f"❌ Lỗi cập nhật: {e}")

    else:
        await query.edit_message_text("Chức năng đang phát triển.")

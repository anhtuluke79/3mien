from telegram import Update
from telegram.ext import ContextTypes
from utils.utils import split_numbers, ghep_xien, dao_so
from utils.can_chi_utils import (
    get_can_chi_ngay,
    sinh_so_hap_cho_ngay,
    phong_thuy_format,
    chot_so_format,
    chuan_hoa_can_chi
)
from utils.thongke_utils import read_xsmb
from handlers.menu import get_ketqua_keyboard

from datetime import datetime

async def all_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    msg = update.message.text.strip()

    # -------- Kết quả xổ số theo ngày --------
    if user_data.get("wait_ketqua_ngay"):
        df = read_xsmb("xsmb.csv")
        try:
            # Chuẩn hóa ngày (hỗ trợ cả dd-mm và yyyy-mm-dd)
            for sep in ["-", "/", "."]:
                if sep in msg:
                    parts = [int(x) for x in msg.split(sep)]
                    break
            else:
                raise ValueError
            if len(parts) == 3:
                if parts[0] > 31:  # yyyy-mm-dd
                    y, m, d = parts
                else:              # dd-mm-yyyy
                    d, m, y = parts
            elif len(parts) == 2:
                d, m = parts
                y = int(df['date'].max()[:4])  # lấy năm mới nhất trong file
            else:
                raise ValueError
            date_str = f"{y}-{m:02d}-{d:02d}"
            row = df[df['date'] == date_str]
            if row.empty:
                raise ValueError
            row = row.iloc[0]
            txt = f"*🎰 KQXSMB ngày {date_str}:*\n"
            txt += f"Đặc biệt: `{row['DB']}`\n"
            txt += f"G1: `{row['G1']}`\n"
            txt += f"G2: `{row['G2']}`\n"
            txt += f"G3: `{row['G3']}`\n"
            txt += f"G4: `{row['G4']}`\n"
            txt += f"G5: `{row['G5']}`\n"
            txt += f"G6: `{row['G6']}`\n"
            txt += f"G7: `{row['G7']}`\n"
            await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=get_ketqua_keyboard())
        except Exception:
            await update.message.reply_text("❗ Không tìm thấy kết quả ngày này, hoặc sai định dạng!", reply_markup=get_ketqua_keyboard())
        user_data.clear()
        return

    # -------- Ghép xiên --------
    if user_data.get('wait_for_xien_input') is not None:
        do_dai = user_data['wait_for_xien_input']
        numbers = split_numbers(msg)
        xiens = ghep_xien(numbers, do_dai)
        if not xiens:
            await update.message.reply_text("⚠️ Không ghép được xiên, vui lòng nhập lại.")
        else:
            reply = f"{len(xiens)} bộ xiên {do_dai}:\n" + ', '.join(xiens[:50])
            await update.message.reply_text(reply)
        user_data.clear()
        return

    # -------- Ghép càng 3D --------
    if user_data.get("wait_cang3d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 2 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 2 chữ số! (VD: 12 34 56)")
            return
        user_data["cang3d_numbers"] = arr
        user_data["wait_cang3d_numbers"] = False
        user_data["wait_cang_input"] = "3D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    # -------- Ghép càng 4D --------
    if user_data.get("wait_cang4d_numbers"):
        arr = split_numbers(msg)
        if not arr or not all(len(n) == 3 for n in arr):
            await update.message.reply_text("⚠️ Mỗi số cần đúng 3 chữ số! (VD: 123 456 789)")
            return
        user_data["cang4d_numbers"] = arr
        user_data["wait_cang4d_numbers"] = False
        user_data["wait_cang_input"] = "4D"
        await update.message.reply_text("📥 Nhập các càng muốn ghép (VD: 1 2 3):")
        return

    # -------- Xử lý ghép càng sau khi đã có dàn --------
    if user_data.get("wait_cang_input"):
        kind = user_data["wait_cang_input"]
        numbers = user_data.get("cang3d_numbers" if kind == "3D" else "cang4d_numbers", [])
        cangs = split_numbers(msg)
        if not cangs:
            await update.message.reply_text("⚠️ Vui lòng nhập ít nhất 1 càng.")
            return
        result = [c + n for c in cangs for n in numbers]
        await update.message.reply_text(f"✅ Ghép {kind}: {len(result)} số\n" + ', '.join(result))
        user_data.clear()
        return

    # -------- Đảo số --------
    if user_data.get("wait_for_dao_input"):
        arr = split_numbers(msg)
        s_concat = ''.join(arr) if arr else msg.replace(' ', '')
        if not s_concat.isdigit() or len(s_concat) < 2 or len(s_concat) > 6:
            await update.message.reply_text("Nhập 1 số có từ 2 đến 6 chữ số (VD: 1234, 56789).")
        else:
            result = dao_so(s_concat)
            if len(result) > 20:
                text = '\n'.join([', '.join(result[i:i+10]) for i in range(0, len(result), 10)])
            else:
                text = ', '.join(result)
            await update.message.reply_text(f"Tổng {len(result)} hoán vị:\n{text}")
        user_data.clear()
        return

    # -------- Phong thủy số theo ngày --------
    if user_data.get('wait_phongthuy'):
        # Tự nhận biết kiểu nhập ngày hay nhập can chi
        try:
            ngay = msg
            # Thử parse ngày
            for sep in ["-", "/", "."]:
                if sep in ngay:
                    parts = [int(x) for x in ngay.split(sep)]
                    break
            else:
                # Không phải số => chắc chắn là can chi
                raise ValueError("canchi")
            now = datetime.now()
            if len(parts) == 3:
                if parts[0] > 31:
                    y, m, d = parts
                else:
                    d, m, y = parts
            elif len(parts) == 2:
                d, m = parts
                y = now.year
            else:
                raise ValueError("dateformat")
            can_chi = get_can_chi_ngay(y, m, d)
            sohap_info = sinh_so_hap_cho_ngay(can_chi)
            text = phong_thuy_format(can_chi, sohap_info)
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            # Có thể là can chi nhập tự do
            try:
                can_chi = chuan_hoa_can_chi(msg)
                sohap_info = sinh_so_hap_cho_ngay(can_chi)
                if sohap_info is None:
                    await update.message.reply_text("❗️ Không tìm thấy thông tin can chi hoặc số hạp với tên bạn nhập! Kiểm tra lại định dạng (VD: Giáp Tý).")
                else:
                    text = phong_thuy_format(can_chi, sohap_info)
                    await update.message.reply_text(text, parse_mode="Markdown")
            except:
                await update.message.reply_text("❗️ Nhập ngày không hợp lệ hoặc can chi sai! Đúng định dạng: YYYY-MM-DD hoặc Giáp Tý.")
        user_data['wait_phongthuy'] = False
        return

    # -------- Góp ý --------
    if user_data.get('wait_for_gopy'):
        text = update.message.text.strip()
        user = update.effective_user
        username = user.username or user.full_name or str(user.id)
        with open("gopy_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {username} | {user.id} | {text}\n")
        await update.message.reply_text(
            "💗 Cảm ơn bạn đã gửi góp ý/ủng hộ! Tất cả phản hồi đều được trân trọng ghi nhận.\n"
            "Bạn có thể tiếp tục sử dụng bot hoặc gửi góp ý thêm bất cứ lúc nào."
        )
        user_data['wait_for_gopy'] = False
        return

    # -------- Broadcast cho admin --------
    if user_data.get("wait_for_broadcast"):
        # Tùy bạn muốn tích hợp thêm code gửi broadcast tới user_list.txt
        await update.message.reply_text("✅ Đã nhận nội dung broadcast (demo).")
        user_data["wait_for_broadcast"] = False
        return

    # Nếu không có trạng thái nào đang chờ, KHÔNG trả lời tin nhắn tự do!
    return

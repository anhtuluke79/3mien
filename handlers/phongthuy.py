from datetime import datetime
from thien_can import CAN_INFO
from can_chi_dict import data as CAN_CHI_SO_HAP

def chuan_hoa_can_chi(s):
    """Chuyển can chi về dạng chuẩn, hoa chữ cái đầu: Giáp Tý, Ất Mão,..."""
    return ' '.join([w.capitalize() for w in s.strip().split()])

def get_can_chi_ngay(year, month, day):
    """Tính can chi ngày dương (lịch Gregory, đầu vào: năm-tháng-ngày)"""
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    chi_list = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
    can = can_list[(jd + 9) % 10]
    chi = chi_list[(jd + 1) % 12]
    return f"{can} {chi}"

def sinh_so_hap_cho_ngay(can_chi_str):
    """
    Sinh số hạp, số mệnh, các bộ số từ can chi truyền vào.
    Trả về dict: can, âm dương, ngũ hành, số hạp can, danh sách số mệnh, các bộ số ghép
    """
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code:
        return None
    so_hap_can, rest = code.split('-')
    so_hap_list = rest.split(',') if rest else []
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    # Tạo các bộ số ghép từ các số mệnh và số hạp
    so_list = [so_hap_can] + so_hap_list
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j:
                ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can,
        "am_duong": info.get("am_duong", "?"),
        "ngu_hanh": info.get("ngu_hanh", "?"),
        "so_hap_can": so_hap_can,
        "so_hap_list": so_hap_list,
        "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    """
    Trả về text phong thủy số dạng đẹp, đồng nhất cho cả ngày/can chi.
    """
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    so_hap_can = sohap_info['so_hap_can'] if sohap_info else "?"
    so_menh = ','.join(sohap_info['so_hap_list']) if sohap_info and sohap_info.get('so_hap_list') else "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and sohap_info.get('so_ghép') else "?"
    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n"
        f"- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n"
        f"- Số hạp ngày: {so_hap_ngay}"
    )
    return text

def chot_so_format(can_chi, sohap_info, today_str):
    """
    Trả về text chốt số miền Bắc (phong thủy) cho ngày hiện tại
    """
    if not sohap_info or not sohap_info.get("so_hap_list"):
        return "Không đủ dữ liệu phong thủy để chốt số hôm nay!"
    d = [sohap_info['so_hap_can']] + sohap_info['so_hap_list']
    chams = ','.join(d)
    dan_de = []
    for x in d:
        for y in d:
            dan_de.append(x + y)
    dan_de = sorted(set(dan_de))
    lo = []
    for x in d:
        for y in d:
            if x != y:
                lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n"
        f"*Chốt số 3 miền ngày {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\n"
        f"Lô: {', '.join(lo)}"
    )
    return text

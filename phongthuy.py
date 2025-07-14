from itertools import combinations, permutations
from can_chi_dict import data as CAN_CHI_SO_HAP
from thien_can import CAN_INFO

def split_numbers(s):
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    if len(numbers) < do_dai: return []
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def dao_so(s):
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(list(perm))

def chuan_hoa_can_chi(s):
    return ' '.join(word.capitalize() for word in s.strip().split())

def get_can_chi_ngay(year, month, day):
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
    code = CAN_CHI_SO_HAP.get(can_chi_str)
    if not code: return None
    so_dau, rest = code.split('-')
    so_ghep = rest.split(',')
    can = can_chi_str.split()[0]
    info = CAN_INFO.get(can, {})
    so_menh = so_dau
    so_list = [so_menh] + so_ghep
    ket_qua = set()
    for i in range(len(so_list)):
        for j in range(len(so_list)):
            if i != j: ket_qua.add(so_list[i] + so_list[j])
    return {
        "can": can, "am_duong": info.get("am_duong"),
        "ngu_hanh": info.get("ngu_hanh"), "so_menh": so_menh,
        "so_hap_list": so_ghep, "so_ghép": sorted(list(ket_qua))
    }

def phong_thuy_format(can_chi, sohap_info, is_today=False, today_str=None):
    can = can_chi.split()[0]
    can_info = CAN_INFO.get(can, {})
    am_duong = can_info.get("am_duong", "?")
    ngu_hanh = can_info.get("ngu_hanh", "?")
    if sohap_info and 'so_hap_list' in sohap_info and len(sohap_info['so_hap_list']) >= 1:
        so_hap_can = sohap_info['so_menh']
        so_menh = ','.join(sohap_info['so_hap_list'])
    else: so_hap_can, so_menh = "?", "?"
    so_hap_ngay = ','.join(sohap_info['so_ghép']) if sohap_info and 'so_ghép' in sohap_info else "?"
    if is_today and today_str:
        main_line = f"🔮 Phong thủy NGÀY HIỆN TẠI: {can_chi} ({today_str})"
    else:
        main_line = f"🔮 Phong thủy số ngũ hành cho ngày {can_chi}:"
    text = (
        f"{main_line}\n- Can: {can}, {am_duong} {ngu_hanh}, số hạp {so_hap_can}\n"
        f"- Số mệnh: {so_menh}\n- Số hạp ngày: {so_hap_ngay}"
    )
    return text

def chot_so_format(can_chi, sohap_info, today_str):
    if not sohap_info or not sohap_info.get("so_hap_list"):
        return "Không đủ dữ liệu phong thủy để chốt số hôm nay!"
    d = [sohap_info['so_menh']] + sohap_info['so_hap_list']
    chams = ','.join(d)
    dan_de = []
    for x in d:
        for y in d:
            dan_de.append(x + y)
    dan_de = sorted(set(dan_de))
    lo = []
    for x in d:
        for y in d:
            if x != y: lo.append(x + y)
    lo = sorted(set(lo))
    icons = "🎉🍀🥇"
    text = (
        f"{icons}\n*Chốt số hôm nay {today_str} ({can_chi})*\n"
        f"Đầu - đuôi (Đặc biệt) - Giải 1: chạm {chams}\n"
        f"Dàn đề: {', '.join(dan_de)}\nLô: {', '.join(lo)}"
    )
    return text

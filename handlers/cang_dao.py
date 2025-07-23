from itertools import permutations

def ghep_cang(numbers, cang_type="3"):
    """Ghép càng cho dàn số. cang_type='3' (ghép càng 3D), '4' (ghép càng 4D)"""
    numbers = [str(n).zfill(2 if cang_type=='3' else 3) for n in numbers]
    result = []
    if cang_type == "3":  # Ghép càng 3D: càng + số 2 chữ số thành 3 chữ số
        for so in numbers:
            for cang in range(10):
                result.append(f"{cang}{so}")
    elif cang_type == "4":  # Ghép càng 4D: càng + số 3 chữ số thành 4 chữ số
        for so in numbers:
            for cang in range(10):
                result.append(f"{cang}{so}")
    return result


def dao_so(so):
    """
    Đảo số: trả về tất cả các hoán vị khác nhau của chuỗi số (tối đa 6 ký tự).
    """
    so = str(so).strip()
    if not (2 <= len(so) <= 6) or not so.isdigit():
        return []
    all_perm = sorted(set("".join(p) for p in permutations(so)))
    return all_perm

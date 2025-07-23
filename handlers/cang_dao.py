from itertools import permutations

def ghep_cang(dan_so, cang):
    """
    Ghép càng vào dàn số.
    - dan_so: list các chuỗi số (2 hoặc 3 số)
    - cang: chuỗi càng muốn ghép (1 hoặc nhiều số, ví dụ: "1", "01", "123")
    Trả về list số mới đã ghép càng.
    """
    cang = str(cang).strip()
    result = [cang + so.zfill(len(so)) for so in dan_so]
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

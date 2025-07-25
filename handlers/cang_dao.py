import re
from itertools import permutations

def clean_numbers_input(text):
    # Nhận số cách nhau bởi dấu cách, phẩy, xuống dòng...
    numbers = re.split(r"[ ,;\n]+", text.strip())
    return [s.zfill(2) for s in numbers if s.isdigit() and len(s) >= 2]

def ghep_cang(numbers, cang):
    """numbers: list số (dàn 2 hoặc 3 chữ số); cang: string 1 số (hoặc nhiều số nếu muốn)"""
    # Nếu user nhập nhiều càng, loop từng càng
    cangs = [str(x) for x in str(cang).replace(",", " ").split() if x.isdigit() and len(x) == 1]
    if not cangs:
        cangs = ["0"]  # Mặc định càng 0 nếu rỗng
    res = []
    for cg in cangs:
        for n in numbers:
            res.append(f"{cg}{n.zfill(3)}")
    return sorted(set(res))

def dao_so(s):
    s = str(s)
    if not s.isdigit() or not (2 <= len(s) <= 6):
        return []
    return sorted(set(["".join(p) for p in permutations(s)]))

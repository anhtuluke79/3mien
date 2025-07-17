import itertools

def split_numbers(s):
    """Tách dãy số từ chuỗi (cách nhau bằng dấu cách hoặc phẩy)."""
    return [n for n in s.replace(',', ' ').split() if n.isdigit()]

def ghep_xien(numbers, do_dai=2):
    """Ghép xiên các số (combinations)."""
    if len(numbers) < do_dai:
        return []
    from itertools import combinations
    result = [tuple(map(str, comb)) for comb in combinations(numbers, do_dai)]
    return ['&'.join(comb) for comb in result]

def ghep_cang(numbers, so_cang=3):
    """
    Ghép càng cho danh sách số (số 2 hoặc 3 chữ số tùy loại càng).
    VD: ghep_cang(['23', '34'], 3) -> ['023', '123', ...]
    """
    if not numbers or len(numbers) == 0:
        return []
    comb = itertools.product(numbers, repeat=so_cang)
    result = [''.join(map(str, tup)) for tup in comb]
    return sorted(set(result))

def dao_so(s):
    """Đảo số, sinh hoán vị tất cả các chữ số trong chuỗi."""
    arr = list(str(s))
    perm = set([''.join(p) for p in itertools.permutations(arr)])
    return sorted(list(perm))

def chuan_hoa_can_chi(s):
    """Viết hoa đầu mỗi từ (dùng cho can chi, ví dụ: giáp tý -> Giáp Tý)."""
    return ' '.join(word.capitalize() for word in s.strip().split())

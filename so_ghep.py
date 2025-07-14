from itertools import combinations, permutations

def tao_xien(numbers, do_dai=2):
    """
    Tạo các bộ xiên từ dãy số đầu vào.
    Args:
        numbers (list): Danh sách các số (str hoặc int)
        do_dai (int): Số lượng số trong mỗi bộ xiên (2, 3, 4...)
    Returns:
        list[str]: Danh sách các bộ xiên. VD: ['12&34', '12&56', ...]
    """
    numbers = [str(x) for x in numbers if str(x).isdigit()]
    if len(numbers) < do_dai:
        return []
    return ['&'.join(comb) for comb in combinations(numbers, do_dai)]

def ghep_cang_3d(numbers, cang_list):
    """
    Ghép các số 2 chữ số với các càng để thành 3D.
    Args:
        numbers (list): Danh sách số 2 chữ số
        cang_list (list): Danh sách càng (chữ số)
    Returns:
        list[str]: VD: ['123', '145', '323', ...]
    """
    numbers = [str(n).zfill(2) for n in numbers if str(n).isdigit()]
    cang_list = [str(c) for c in cang_list if str(c).isdigit()]
    return [c + n for c in cang_list for n in numbers]

def ghep_cang_4d(numbers, cang_list):
    """
    Ghép các số 3 chữ số với các càng để thành 4D.
    Args:
        numbers (list): Danh sách số 3 chữ số
        cang_list (list): Danh sách càng (chữ số)
    Returns:
        list[str]: VD: ['1123', '1456', ...]
    """
    numbers = [str(n).zfill(3) for n in numbers if str(n).isdigit()]
    cang_list = [str(c) for c in cang_list if str(c).isdigit()]
    return [c + n for c in cang_list for n in numbers]

def dao_so(s):
    """
    Trả về tất cả các hoán vị (không trùng) các chữ số của số s.
    Args:
        s (str or int): Số đầu vào (chuỗi hoặc int)
    Returns:
        list[str]: VD: ['123', '132', '213', ...]
    """
    s = ''.join(str(x) for x in str(s) if str(x).isdigit())
    if not s or len(s) < 2:
        return []
    arr = list(s)
    perm = set([''.join(p) for p in permutations(arr)])
    return sorted(perm)

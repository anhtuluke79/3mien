def clean_numbers_input(text):
    """
    Chuẩn hóa input: tách dàn số/càng bằng dấu cách, phẩy, xuống dòng, v.v.
    Trả về list chuỗi số, loại bỏ rỗng, giữ nguyên thứ tự.
    """
    for sep in [",", "\n", ";"]:
        text = text.replace(sep, " ")
    nums = [s.strip() for s in text.split() if s.strip()]
    return nums

def ghep_cang(numbers, cangs):
    """
    Ghép từng càng (list hoặc chuỗi) vào đầu mỗi số trong dàn.
    numbers: list các số (chuỗi) — đã được chuẩn hóa số chữ số (2 hoặc 3)
    cangs: list các càng (chuỗi, có thể là 1 hoặc nhiều càng, có thể là số bất kỳ)
    Trả về list các số (chuỗi) sau khi ghép.
    """
    results = []
    for so in numbers:
        for c in cangs:
            results.append(f"{c}{so}")
    return results

def dao_so(number):
    """
    Trả về mọi hoán vị (permutation) của số đầu vào (2-6 chữ số).
    """
    from itertools import permutations
    number = str(number)
    if not number.isdigit() or not (2 <= len(number) <= 6):
        return []
    perms = set("".join(p) for p in permutations(number))
    perms.discard(number)  # bỏ chính số gốc nếu muốn
    return sorted(perms)

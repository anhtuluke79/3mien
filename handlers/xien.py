from itertools import combinations

def clean_numbers_input(input_str):
    """
    Chuẩn hóa chuỗi input: tách các số bằng dấu cách, phẩy hoặc xuống dòng.
    Trả về list các số (chuỗi 2 chữ số).
    """
    items = input_str.replace(",", " ").replace("\n", " ").split()
    return [s.zfill(2) for s in items if s.strip().isdigit()]

def gen_xien(numbers, n):
    """Sinh tổ hợp xiên n từ dàn numbers (danh sách chuỗi số)."""
    if len(numbers) < n:
        return []
    combos = list(combinations(numbers, n))
    return combos

def format_xien_result(combos):
    """Định dạng kết quả ghép xiên trả về Telegram."""
    lines = [", ".join(combo) for combo in combos]
    if not lines:
        return "❗ Không đủ số để ghép xiên."
    return "*Kết quả tổ hợp xiên:*\n" + "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))

import sys
import os

# Tự động thêm root vào sys.path để import file ngoài root (nếu chạy từ handlers/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from thien_can import CAN_INFO
from can_chi_dict import data as CAN_CHI_DATA

def phongthuy_ngay(can:str, chi:str):
    """
    Trả về thông tin phong thủy cho ngày dựa trên thiên can, địa chi.
    """
    info = CAN_INFO.get(can, None)
    if not info:
        return f"Không tìm thấy thông tin thiên can {can}."
    key = f"{can} {chi}"
    so_goi_y = CAN_CHI_DATA.get(key, "Không rõ")
    return (
        f"🌟 Ngày {can} {chi}\n"
        f"- Âm/Dương: {info['am_duong']}\n"
        f"- Ngũ hành: {info['ngu_hanh']}\n"
        f"- Phương: {info['phuong']}\n"
        f"- Số gợi ý: {so_goi_y}"
    )

def phongthuy_can_chi(can_chi:str):
    """
    Tra cứu số hợp từ dict can_chi_dict.py cho can chi bất kỳ.
    """
    so_goi_y = CAN_CHI_DATA.get(can_chi, None)
    if so_goi_y:
        return f"Can chi {can_chi} - Số hợp: {so_goi_y}"
    else:
        return f"Không tìm thấy số hợp cho can chi {can_chi}."

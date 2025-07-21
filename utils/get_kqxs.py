import requests
from bs4 import BeautifulSoup

def get_kqxs(region='mb'):
    urls = {
        'mb': 'https://www.minhngoc.com.vn/kqxs/mien-bac.html',
        'mn': 'https://www.minhngoc.com.vn/ket-qua-xo-so/mien-nam.html',
        'mt': 'https://www.minhngoc.com.vn/ket-qua-xo-so/mien-trung.html'
    }
    url = urls.get(region, urls['mb'])
    r = requests.get(url, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')

    # Lấy ngày (Minh Ngọc để ngày ở dòng có class 'tngay')
    date_tag = soup.select_one('td.tngay')
    date = date_tag.text.strip() if date_tag else 'Hôm nay'

    # Kết quả các giải (dựa trên class từng giải, phù hợp XSMB/MN/MT)
    giai_list = [
        ('G8', 'giai8'), ('G7', 'giai7'), ('G6', 'giai6'),
        ('G5', 'giai5'), ('G4', 'giai4'), ('G3', 'giai3'),
        ('G2', 'giai2'), ('G1', 'giai1'), ('ĐB', 'giaidb')
    ]
    result_lines = [f"*KQXS {'MB' if region == 'mb' else ('MN' if region == 'mn' else 'MT')} {date}*"]
    for label, giai in giai_list:
        numbers = [span.text.strip() for span in soup.select(f'td.{giai} span')]
        if numbers:
            result_lines.append(f"{label}: {'  '.join(numbers)}")
    return '\n'.join(result_lines)

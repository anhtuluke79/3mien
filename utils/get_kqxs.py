import requests
from bs4 import BeautifulSoup

def get_kqxs(region='mb'):
    region_map = {
        'mb': 'mien-bac',
        'mn': 'mien-nam',
        'mt': 'mien-trung'
    }
    url = f"https://minhchinh.com/xo-so-{region_map.get(region, 'mien-bac')}/"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    date_div = soup.find('div', class_='thong_tin_ngay')
    date = date_div.text.strip() if date_div else "?"
    result_lines = [f"*KQXS {'MB' if region=='mb' else ('MN' if region=='mn' else 'MT')} {date}*"]
    table = soup.find('table', class_='bkqmienbac' if region == 'mb' else 'bkqmiennam' if region == 'mn' else 'bkqmientrung')
    if not table:
        return "Không lấy được dữ liệu từ minhchinh.com!"
    rows = table.find_all('tr')[1:]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            label = cells[0].text.strip()
            numbers = ' '.join(c.text.strip() for c in cells[1:])
            result_lines.append(f"{label}: `{numbers}`")
    return '\n'.join(result_lines)

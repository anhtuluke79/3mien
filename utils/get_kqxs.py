import requests
from bs4 import BeautifulSoup

def get_kqxs(region='mb'):
    url = {
        'mb': 'https://ketqua.net/xo-so-mien-bac',
        'mn': 'https://ketqua.net/xo-so-mien-nam',
        'mt': 'https://ketqua.net/xo-so-mien-trung'
    }.get(region, 'mb')
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    date = soup.find('td', class_='ngay').text.strip()
    bang = soup.find('table', class_='kqmb' if region == 'mb' else 'kqmien')
    rows = bang.find_all('tr')[1:]
    result_lines = [f"*KQXS {'MB' if region == 'mb' else ('MN' if region == 'mn' else 'MT')} {date}*"]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            label = cells[0].text.strip()
            numbers = ' '.join(c.text.strip() for c in cells[1:])
            result_lines.append(f"{label}: `{numbers}`")
    return '\n'.join(result_lines)

import requests
import re
from bs4 import BeautifulSoup

def get_boat_data(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        # 気象データ (気温、風速、水温、波高)
        weather_data = soup.select('.weatherBox_data')
        weather = [re.sub(r'[^0-9.]', '', tag.text) for tag in weather_data]
        return {"ex_times": [float(t) for t in ex_times], "weather": weather}
    except:
        return None

if __name__ == "__main__":
    # 下関12Rのテスト
    print(get_boat_data("19", "12"))

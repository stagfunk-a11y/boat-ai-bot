import requests
import re
from bs4 import BeautifulSoup
import time

# 全国24会場のJCDコードリスト
JCD_LIST = [str(i).zfill(2) for i in range(1, 25)]

def get_boat_data(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 展示タイム取得
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        
        if not ex_times: # データがなければスキップ
            return None
            
        # 気象データ
        weather_data = soup.select('.weatherBox_data')
        weather = [re.sub(r'[^0-9.]', '', tag.text) for tag in weather_data]
        
        return {
            "jcd": jcd,
            "rno": rno,
            "ex_times": [float(t) for t in ex_times],
            "weather": weather
        }
    except:
        return None

if __name__ == "__main__":
    print("🚀 全会場のスキャンを開始します...")
    for jcd in JCD_LIST:
        # 各会場の1Rから12Rまでチェック（効率化のため直近レースのみに絞ることも可能）
        for rno in range(1, 13):
            data = get_boat_data(jcd, str(rno))
            if data:
                print(f"✅ 会場{jcd} {rno}R のデータを取得しました: {data}")
                # ここにLINE送信や予想ロジックを繋げます
            
            # サーバーに負荷をかけないよう少し待機
            time.sleep(0.5)
    print("🏁 スキャン完了")

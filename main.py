import requests
import re
from bs4 import BeautifulSoup
import time
import os

# --- 設定 ---
# 確実に起動(Live)させるため、LINE機能は一旦外しています。
# ステータスが緑の Live になった後、改めて LINE を繋ぎ込みます。

# 全国24会場のJCDコードリスト
JCD_LIST = [str(i).zfill(2) for i in range(1, 25)]

def get_boat_data(jcd, rno):
    """展示タイムと気象データを取得"""
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 展示タイム取得
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        if not ex_times or len(ex_times) < 6:
            return None
            
        # 気象データ
        weather_data = soup.select('.weatherBox_data')
        weather = [re.sub(r'[^0-9.]', '', tag.text) for tag in weather_data]
        
        return {
            "jcd": jcd,
            "rno": rno,
            "ex_times": ex_times,
            "weather": weather
        }
    except:
        return None

if __name__ == "__main__":
    print("🚀 ボートレース監視システム、起動しました")
    
    while True:
        current_hour = time.localtime().tm_hour
        
        # 深夜（21時〜翌8時）は1時間おきにチェック（節約モード）
        if current_hour >= 21 or current_hour < 8:
            print("🌙 夜間モード：1時間待機します...")
            time.sleep(3600)
            continue

        print(f"⏰ {current_hour}時台のスキャンを開始します...")
        
        for jcd in JCD_LIST:
            for rno in range(1, 13):
                data = get_boat_data(jcd, str(rno))
                if data:
                    # 今はログに出力するだけ
                    print(f"✅ データ確認: 会場{jcd} {rno}R {data['ex_times']}")
                
                time.sleep(0.1) 
        
        print("🏁 全会場チェック完了。10分後に再試行します。")
        time.sleep(600)

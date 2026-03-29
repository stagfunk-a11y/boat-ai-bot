import requests
import re
from bs4 import BeautifulSoup
import time
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定（Renderの環境変数から読み込み） ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# 全国24会場のJCDコードリスト
JCD_LIST = [str(i).zfill(2) for i in range(1, 25)]

def get_boat_data(jcd, rno):
    """ボートレース公式サイトから展示タイムと気象データを取得"""
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

def send_line_message(data):
    """LINEに予想（テスト版）を送信"""
    # ここに藤井さんの予想ロジックを入れる予定。今はデータ通知のみ。
    msg = f"【ボートレース予想】\n会場コード:{data['jcd']}\nレース:{data['rno']}R\n展示タイム:{data['ex_times']}\n気象:{data['weather']}"
    try:
        # ブロードキャスト送信（友だち登録者全員に届きます）
        line_bot_api.broadcast(TextSendMessage(text=msg))
        print(f"📢 LINE送信完了: {data['jcd']} {data['rno']}R")
    except Exception as e:
        print(f"❌ LINE送信失敗: {e}")

if __name__ == "__main__":
    print("🚀 ボートレースAIボット、24会場監視モードで起動しました")
    
    # 送信済みレースを記録するリスト（同じレースを何度も送らないため）
    sent_list = []

    while True:
        current_hour = time.localtime().tm_hour
        
        # 深夜（21時〜翌8時）は1時間おきにチェック（節約モード）
        if current_hour >= 21 or current_hour < 8:
            print("🌙 夜間モード：1時間待機します...")
            time.sleep(3600)
            sent_list = [] # 日付が変わるタイミングでリストをリセット
            continue

        print(f"⏰ {current_hour}時台のスキャンを開始します...")
        
        for jcd in JCD_LIST:
            for rno in range(1, 13):
                race_id = f"{jcd}-{rno}"
                if race_id in sent_list:
                    continue
                
                data = get_boat_data(jcd, str(rno))
                if data:
                    send_line_message(data)
                    sent_list.append(race_id) # 送信済みに追加
                
                time.sleep(0.2) # サイトへの負荷軽減
        
        print("🏁 全会場チェック完了。5分後に再試行します。")
        time.sleep(300) # 5分待機

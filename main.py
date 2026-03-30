import os
import requests
import re
from bs4 import BeautifulSoup
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None

# --- 窓口（LINE検証用） ---
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    server.serve_forever()

# --- データ取得 ---
def get_exhibition_data(jcd, rno):
    """展示タイムと展示進入を取得"""
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        # 展示タイム（6.xx または 7.xx）を6人分抽出
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        return ex_times if len(ex_times) == 6 else None
    except:
        return None

def get_active_venues():
    """今日開催されている会場コードを取得"""
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    try:
        res = requests.get(url, timeout=10)
        # 会場コード(jcd) 01〜24 を抽出
        venues = re.findall(r'jcd=(\d{2})', res.text)
        return sorted(list(set(venues)))
    except:
        return []

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("🚀 全国24会場スキャン・フル稼働開始！")
    
    while True:
        current_hour = time.localtime().tm_hour
        if 8 <= current_hour <= 21:
            venues = get_active_venues()
            print(f"📡 現在開催中の会場: {venues}")
            
            for jcd in venues:
                # 各会場の直近レース(1R〜12R)をスキャン
                # ※効率化のため、まずは各会場の「今」のデータを1つずつチェック
                for rno in range(1, 13):
                    r_str = str(rno).zfill(1)
                    data = get_exhibition_data(jcd, r_str)
                    
                    if data:
                        # 展示データがあればLINE送信
                        msg = f"【速報】会場:{jcd} {rno}R\n展示タイム: {', '.join(data)}"
                        try:
                            line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                            print(f"📩 送信済: 会場{jcd} {rno}R")
                        except:
                            pass
                        time.sleep(1) # LINE連続送信制限対策
            
        print("💤 全会場スキャン完了。10分待機します...")
        time.sleep(600)

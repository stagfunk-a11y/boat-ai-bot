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

# --- LINEの信号（POST）を受け止めるための窓口 ---
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        # LINEからの「検証」や「メッセージ」に応答する
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    print(f"📡 窓口を開放しました（Port:{port}）")
    server.serve_forever()

def get_boat_data(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        return ex_times if len(ex_times) == 6 else None
    except:
        return None

if __name__ == "__main__":
    # サーバーを別スレッドで開始
    threading.Thread(target=run_server, daemon=True).start()
    
    print("🚀 ボートレース監視システム、稼働中！")
    
    while True:
        # 8時〜21時の間、15分おきに下関のデータを送ってみる
        current_hour = time.localtime().tm_hour
        if 8 <= current_hour <= 21:
            data = get_boat_data("19", "01") # 下関 1R
            if data and line_bot_api and USER_ID:
                try:
                    msg = f"【開通テスト】下関 1R\n展示タイム: {', '.join(data)}"
                    line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                    print("📩 LINE送信成功")
                except Exception as e:
                    print(f"❌ 送信エラー: {e}")
        
        print("💤 15分待機...")
        time.sleep(900)

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
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
USER_ID = os.environ.get('LINE_USER_ID') # 自分のLINEユーザーID

# Renderのタイムアウト回避用
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def get_boat_data(jcd, rno):
    """指定した会場・レースの展示タイムを取得"""
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
    # 窓口開放
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    print("🚀 ボートレース監視システム、フル稼働開始！")
    
    while True:
        current_hour = time.localtime().tm_hour
        # 8時〜21時の間だけ稼働
        if 8 <= current_hour <= 21:
            for jcd in [str(i).zfill(2) for i in range(1, 25)]:
                # 各会場の1R〜12Rをチェック（簡易版として直近レースを想定）
                # ※本来は締切時刻を見て制御しますが、まずはデータを取ることを優先
                data = get_boat_data(jcd, "01") 
                if data:
                    msg = f"【データ取得】会場:{jcd} 1R\n展示タイム: {', '.join(data)}"
                    line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                    print(f"📩 LINE送信済: {jcd}")
                time.sleep(1) # サーバー負荷軽減
        
        print("💤 15分待機します...")
        time.sleep(900)

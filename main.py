import os
import requests
import re
from bs4 import BeautifulSoup
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定（Renderの環境変数から読み込み） ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('LINE_USER_ID')

# LINE通信の準備
if CHANNEL_ACCESS_TOKEN:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# Renderのタイムアウト回避用の窓口
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
    """展示タイムを取得"""
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        # ここで BeautifulSoup を使います（requirements.txt に bs4 が必要）
        soup = BeautifulSoup(res.text, 'html.parser')
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        return ex_times if len(ex_times) == 6 else None
    except:
        return None

if __name__ == "__main__":
    # 窓口を別スレッドで開始
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    print("🚀 ボートレース監視システム、フル稼働開始！")
    
    while True:
        # 下関（19）の 1R をテストで取得してみる
        data = get_boat_data("19", "01")
        
        if data and CHANNEL_ACCESS_TOKEN and USER_ID:
            msg = f"【テスト成功】下関 1R\n展示: {', '.join(data)}"
            try:
                line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                print("📩 LINE送信成功！")
            except Exception as e:
                print(f"❌ LINE送信失敗: {e}")
        
        print("💤 15分待機します...")
        time.sleep(900)

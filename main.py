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

# --- データ取得関数 ---
def get_exhibition_data(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        return ex_times if len(ex_times) == 6 else None
    except:
        return None

def get_active_venues():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    try:
        res = requests.get(url, timeout=10)
        venues = re.findall(r'jcd=(\d{2})', res.text)
        return sorted(list(set(venues)))
    except:
        return []

if __name__ == "__main__":
    # 1. サーバーを別スレッドで起動
    threading.Thread(target=run_server, daemon=True).start()
    
    print("🚀 システム起動プロセス開始...")
    
    # ★★★ 【最重要】起動した瞬間に藤井さんに挨拶を送る ★★★
    if line_bot_api and USER_ID:
        try:
            test_msg = "藤井さん、お待たせしました！\ntakumi ai 起動しました。これで通信は完璧です！🚀"
            line_bot_api.push_message(USER_ID, TextSendMessage(text=test_msg))
            print("📩 【成功】テストメッセージを送信しました！")
        except Exception as e:
            print(f"❌ 【失敗】LINE送信エラー: {e}")
    else:
        print("⚠️ IDまたはトークンが設定されていません。")

    # 2. 全国スキャンループ
    while True:
        current_hour = time.localtime().tm_hour
        if 8 <= current_hour <= 21:
            venues = get_active_venues()
            for jcd in venues:
                # 1Rから12Rまでスキャン
                for rno in range(1, 13):
                    data = get_exhibition_data(jcd, str(rno))
                    if data:
                        msg = f"【速報】会場:{jcd} {rno}R\n展示タイム: {', '.join(data)}"
                        try:
                            line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                        except:
                            pass
                        time.sleep(1)
            
        print("💤 スキャン完了。15分待機します...")
        time.sleep(900)

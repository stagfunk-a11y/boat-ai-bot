import os, requests, re, time, threading
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None

# --- 窓口（Render維持用） ---
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_POST(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    server.serve_forever()

# --- 超・積極的データ取得 ---
def get_any_exhibition(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        # 6.xx または 7.xx の数字を全部拾う
        times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)
        # チルトっぽい数字も拾う
        tilts = re.findall(r'[+-][01]\.[05]', res.text)
        return {"times": times, "tilts": tilts} if times else None
    except:
        return None

def get_venues():
    try:
        res = requests.get("https://www.boatrace.jp/owpc/pc/race/index", timeout=10)
        return sorted(list(set(re.findall(r'jcd=(\d{2})', res.text))))
    except:
        return []

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    
    # 起動確認
    if line_bot_api and USER_ID:
        line_bot_api.push_message(USER_ID, TextSendMessage(text="🛠️ 修正版システム、再起動しました。全会場スキャンを開始します！"))

    sent_list = []
    while True:
        venues = get_venues()
        print(f"📡 スキャン開始: {len(venues)}会場")
        
        for jcd in venues:
            # 1R〜12Rまで全部見る
            for rno in range(1, 13):
                race_key = f"{jcd}-{rno}-{time.strftime('%H')}"
                if race_key in sent_list: continue

                info = get_any_exhibition(jcd, rno)
                if info:
                    msg = f"【速報】会場:{jcd} {rno}R\n展示: {' / '.join(info['times'])}\nチルト: {' '.join(info['tilts'])}"
                    try:
                        line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                        sent_list.append(race_key)
                        print(f"✅ 送信完了: {jcd} {rno}R")
                    except Exception as e:
                        print(f"❌ LINE送信エラー: {e}")
                time.sleep(1) # サイトに負荷をかけないよう少し待つ

        # リストが溜まりすぎたらリセット
        if len(sent_list) > 200: sent_list = []
        
        print("💤 一巡完了。5分後にまたスキャンします。")
        time.sleep(300) # 間隔を5分に短縮

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

# --- 会場データ（過去の統計：1コース1着率など） ---
VENUE_DATA = {
    "12": {"name": "下関", "1_win_rate": 60, "characteristic": "ナイター・イン強め"},
    "17": {"name": "宮島", "1_win_rate": 55, "characteristic": "潮の干満差あり"},
    # 他の会場も同様に追加可能
}

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

# --- 直前情報（タイム・チルト・部品）の取得 ---
def get_detailed_info(jcd, rno):
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 展示タイム抽出
        ex_times = re.findall(r'6\.\d{2}|7\.\d{2}', res.text)[:6]
        # チルト抽出
        tilts = re.findall(r'[\-\+]?\d\.\d', res.text)[:6]
        # 部品交換（簡易検知）
        parts = "なし" if "部品交換" not in res.text else "あり(要確認)"
        
        return {"times": ex_times, "tilts": tilts, "parts": parts}
    except:
        return None

# --- 🎯 三連単予想ロジック ---
def generate_prediction(jcd, rno, info):
    times = [float(t) for t in info["times"]]
    best_time = min(times)
    best_boat = times.index(best_time) + 1
    
    venue = VENUE_DATA.get(jcd, {"name": jcd, "1_win_rate": 50})
    
    # ロジック：1号艇がそこまで遅くなく、インが強い会場なら1軸
    if times[0] <= best_time + 0.05 and venue["1_win_rate"] >= 55:
        return f"【本命】1-{best_boat}-流し / 1-流し-{best_boat}"
    # ロジック：外枠に爆速タイムがいる場合
    elif best_boat >= 3:
        return f"【穴狙い】{best_boat}-1-流し / {best_boat}-流し-1"
    else:
        return "【混戦】展示気配重視。広めに検討"

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("🚀 予想AIシステム起動...")
    
    sent_list = []
    while True:
        current_hour = time.localtime().tm_hour
        if 8 <= current_hour <= 21:
            venues = ["12", "17", "18", "19"] # 主要な会場コード（下関・宮島・徳山・芦屋など）
            for jcd in venues:
                for rno in range(1, 13):
                    race_id = f"{jcd}_{rno}_{time.strftime('%H')}"
                    if race_id in sent_list: continue

                    info = get_detailed_info(jcd, str(rno))
                    if info and len(info["times"]) == 6:
                        # 予想生成
                        pred = generate_prediction(jcd, rno, info)
                        
                        v_name = VENUE_DATA.get(jcd, {"name": jcd})["name"]
                        msg = f"🤖 AI予想: {v_name} {rno}R\n"
                        msg += f"展示: {' '.join(info['times'])}\n"
                        msg += f"チルト: {' '.join(info['tilts'])}\n"
                        msg += f"部品: {info['parts']}\n"
                        msg += f"━━━━━━━━━━\n"
                        msg += f"🎯 推奨: {pred}"
                        
                        try:
                            line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                            sent_list.append(race_id)
                        except: pass
                        time.sleep(1)
            
            if len(sent_list) > 100: sent_list = sent_list[-50:]

        print("💤 スキャン完了。10分待機...")
        time.sleep(600)

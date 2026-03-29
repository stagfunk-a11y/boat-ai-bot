import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import time

# --- Renderのタイムアウトを回避するための「偽の窓口」 ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"📡 偽の窓口をポート {port} で開放しました")
    server.serve_forever()

# --- メインの監視プログラム ---
if __name__ == "__main__":
    # 偽の窓口を別スレッドで開始
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    print("🚀 ボートレース監視システム、起動しました")
    
    while True:
        try:
            res = requests.get("https://www.boatrace.jp/", timeout=10)
            print(f"✅ 接続チェックOK: {res.status_code}")
        except Exception as e:
            print(f"❌ 接続エラー: {e}")
            
        print("🌙 待機中（10分おきにチェック）...")
        time.sleep(600)

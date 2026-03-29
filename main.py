import requests
import time

if __name__ == "__main__":
    print("🚀 ボートレース監視システム（超軽量版）、起動しました")
    
    while True:
        # 公式サイトにアクセスできるかだけチェック
        try:
            res = requests.get("https://www.boatrace.jp/", timeout=10)
            print(f"✅ 接続チェックOK: {res.status_code}")
        except:
            print("❌ 接続エラー")
            
        print("🌙 夜間モード：10分待機します...")
        time.sleep(600)

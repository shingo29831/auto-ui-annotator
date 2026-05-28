# AI-ROLE: アプリケーションのエントリーポイント
import sys
import time
from src.config import TARGET_URLS_FILE, VISITED_URLS_FILE, MAX_PAGES_TO_SCRAPE
from src.url_manager import UrlManager
from src.crawler import crawl_site

def main():
    url_manager = UrlManager(TARGET_URLS_FILE, VISITED_URLS_FILE)
    
    print(f"=== スクレイピング監視を開始します ===")
    print(f"ヒント: 実行中に {TARGET_URLS_FILE} へ新しいURLを追記すると自動で検知します。\n終了するには Ctrl+C を押してください。")
    
    try:
        while True:
            # なぜ: 実行中に追加された新しいURLをリアルタイムで取得するため毎回読み直す
            target_urls = url_manager.load_target_urls()
            new_urls_found = False
            
            for url in target_urls:
                # なぜ: target_urls.txt に記述されているが、まだ訪問済み(visited)になっていないURLだけを処理するため
                if not url_manager.is_visited(url):
                    print(f"\n=== 新しいターゲットを発見: {url} のスクレイピングを開始します ===")
                    crawl_site(url, url_manager, MAX_PAGES_TO_SCRAPE)
                    new_urls_found = True
                    
            if not new_urls_found:
                # なぜ: 新しいURLが無い場合にCPUリソースを無駄に消費する(ビジーループ)のを防ぐため
                time.sleep(5)
                
    except KeyboardInterrupt:
        # なぜ: ユーザーがCtrl+Cで安全にプログラムを終了できるようにするため
        print("\n=== 監視プロセスを終了します ===")
        sys.exit(0)

if __name__ == "__main__":
    main()
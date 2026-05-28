# AI-ROLE: アプリケーションのエントリーポイント
import sys
from src.config import TARGET_URLS_FILE, VISITED_URLS_FILE, MAX_PAGES_TO_SCRAPE
from src.url_manager import UrlManager
from src.crawler import crawl_site

def main():
    url_manager = UrlManager(TARGET_URLS_FILE, VISITED_URLS_FILE)
    target_urls = url_manager.load_target_urls()
    
    if not target_urls:
        print(f"エラー: {TARGET_URLS_FILE} にURLが設定されていません。")
        sys.exit(1)
        
    for url in target_urls:
        print(f"=== {url} のスクレイピングを開始します ===")
        crawl_site(url, url_manager, MAX_PAGES_TO_SCRAPE)

if __name__ == "__main__":
    main()
# AI-ROLE: 非同期ワーカーを用いた並列スクレイピングの監視・統括エントリーポイント
import asyncio
import sys
from playwright.async_api import async_playwright
from src.config import TARGET_URLS_FILE, VISITED_URLS_FILE, MAX_PAGES_TO_SCRAPE, MAX_CONCURRENT_SITES, BALANCER_TARGET_LIMIT, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
from src.url_manager import UrlManager
from src.balancer import DatasetBalancer
from src.crawler import crawl_site

async def worker(worker_id: int, queue: asyncio.Queue, url_manager: UrlManager, balancer: DatasetBalancer, context):
    # なぜ: 監視ループからQueueに積まれたURLを並列で取り出し、継続的に処理する非同期コンシューマー
    while True:
        url = await queue.get()
        print(f"\n[Worker-{worker_id}] 新しいターゲットのスクレイピングを開始: {url}")
        try:
            await crawl_site(url, url_manager, balancer, context, MAX_PAGES_TO_SCRAPE)
        except Exception as e:
            print(f"[Worker-{worker_id}] 予期せぬエラー: {e}")
        finally:
            queue.task_done()

async def async_main():
    url_manager = UrlManager(TARGET_URLS_FILE, VISITED_URLS_FILE)
    balancer = DatasetBalancer(BALANCER_TARGET_LIMIT)
    queue = asyncio.Queue()
    enqueued_urls = set()
    
    print(f"=== 非同期並列スクレイピング監視を開始します (並列数: {MAX_CONCURRENT_SITES}) ===")
    print(f"ヒント: 実行中に {TARGET_URLS_FILE} へ新しいURLを追記すると自動検知します。\n終了時は Ctrl+C を押してください。")
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        # なぜ: 単一のブラウザコンテキストを複数のワーカーで共有し、メモリ消費を抑えつつ高速化を図るため
        context = await browser.new_context(viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        
        workers = [
            asyncio.create_task(worker(i, queue, url_manager, balancer, context))
            for i in range(MAX_CONCURRENT_SITES)
        ]
        
        try:
            # なぜ: target_urls.txt の変更をリアルタイムで検知し Queue に供給するプロデューサー
            while True:
                target_urls = url_manager.load_target_urls()
                for url in target_urls:
                    if url not in enqueued_urls and not url_manager.is_visited(url):
                        await queue.put(url)
                        enqueued_urls.add(url)
                
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        finally:
            print("\nワーカータスクを終了しブラウザをクローズします...")
            for w in workers:
                w.cancel()
            await browser.close()

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n=== 監視プロセスを安全に終了しました ===")
        sys.exit(0)

if __name__ == "__main__":
    main()
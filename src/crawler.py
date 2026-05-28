# AI-ROLE: ページ遷移、スクロール、スクリーンショット保存などのブラウザ操作を統括するモジュール
import os
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from src.config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, OUTPUT_IMG_DIR, OUTPUT_LBL_DIR, TIMEOUT_MS, MAX_RETRIES
from src.extractor import extract_elements
from src.url_manager import UrlManager

def auto_scroll(page):
    # なぜ: 動的コンテンツ（遅延読み込み画像や無限スクロール要素）をレンダリングさせるため
    page.evaluate("""() => {
        return new Promise((resolve) => {
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                if(totalHeight >= scrollHeight - window.innerHeight){
                    clearInterval(timer);
                    window.scrollTo(0, 0);
                    resolve();
                }
            }, 100);
        });
    }""")

def crawl_site(start_url: str, url_manager: UrlManager, max_pages: int):
    queue = [start_url]
    page_count = 0

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        page = context.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        while queue and page_count < max_pages:
            current_url = queue.pop(0)
            
            if url_manager.is_visited(current_url):
                continue
                
            page_count += 1
            print(f"[{page_count}/{max_pages}] 処理中: {current_url}")
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    # なぜ: React等のSPAで完全にDOMが構築され通信が落ち着くまで待機するため
                    page.goto(current_url, wait_until="networkidle")
                    
                    auto_scroll(page)
                    page.wait_for_timeout(1000) # なぜ: 最終的なアニメーションやレイアウトの再計算を待つため
                    
                    page.evaluate("document.body.style.overflow = 'hidden';")
                    
                    # なぜ: 複数サイトのスクレイピングを中断・再開した際、ファイル名が衝突するのを防ぐため
                    timestamp = int(time.time() * 1000)
                    base_filename = f"scraped_{timestamp}_{page_count:05d}"
                    img_path = os.path.join(OUTPUT_IMG_DIR, f"{base_filename}.jpg")
                    lbl_path = os.path.join(OUTPUT_LBL_DIR, f"{base_filename}.txt")
                    
                    page.screenshot(path=img_path, type="jpeg", quality=90)
                    
                    elements = extract_elements(page)
                    with open(lbl_path, "w", encoding="utf-8") as f:
                        for el in elements:
                            f.write(f"{el['class_id']} {el['x']:.6f} {el['y']:.6f} {el['w']:.6f} {el['h']:.6f}\n")
                            
                    print(f"  -> {len(elements)} 個の要素を抽出しました。")
                    url_manager.mark_as_visited(current_url)
                    
                    hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
                    for href in hrefs:
                        full_url = urljoin(current_url, href)
                        if url_manager.is_valid_url(start_url, full_url) and not url_manager.is_visited(full_url):
                            queue.append(full_url)
                            
                    success = True
                    break 
                except PlaywrightTimeoutError:
                    print(f"  -> [警告] タイムアウト (試行 {attempt + 1}/{MAX_RETRIES}): {current_url}")
                except Exception as e:
                    print(f"  -> [エラー] 例外発生 (試行 {attempt + 1}/{MAX_RETRIES}): {e}")
                    
            if not success:
                print(f"  -> [失敗] {MAX_RETRIES}回の試行に失敗しました: {current_url}")

        browser.close()
        print(f"\n完了: {start_url} から合計 {page_count} ページを処理しました。")
    
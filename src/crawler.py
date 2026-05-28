# AI-ROLE: ページ遷移、スクロール、スクリーンショット保存などのブラウザ操作を統括するモジュール
import os
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from src.config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, OUTPUT_IMG_DIR, OUTPUT_LBL_DIR, TIMEOUT_MS, MAX_RETRIES
from src.extractor import extract_elements, restore_hidden_elements
from src.url_manager import UrlManager

def crawl_site(start_url: str, url_manager: UrlManager, max_pages: int):
    queue = [start_url]
    page_count = 0
    seen_element_hashes = set() 

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
                    page.goto(current_url, wait_until="networkidle")
                    
                    page.evaluate("""() => {
                        return new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 500;
                            const timer = setInterval(() => {
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if(totalHeight >= document.body.scrollHeight){
                                    clearInterval(timer);
                                    window.scrollTo(0, 0); 
                                    resolve();
                                }
                            }, 100);
                        });
                    }""")
                    page.wait_for_timeout(1000)
                    
                    page.add_style_tag(content="::-webkit-scrollbar { display: none !important; } * { scrollbar-width: none !important; }")
                    
                    total_height = page.evaluate("document.body.scrollHeight")
                    if total_height == 0:
                        total_height = VIEWPORT_HEIGHT
                    
                    for theme in ["light", "dark"]:
                        page.emulate_media(color_scheme=theme)
                        page.evaluate(f"""(currentTheme) => {{
                            if (currentTheme === 'dark') {{
                                document.documentElement.classList.add('dark');
                                document.documentElement.setAttribute('data-theme', 'dark');
                            }} else {{
                                document.documentElement.classList.remove('dark');
                                document.documentElement.setAttribute('data-theme', 'light');
                            }}
                        }}""", theme)
                        page.wait_for_timeout(1000)
                        
                        current_y = 0
                        screen_index = 0
                        
                        while current_y < total_height:
                            page.evaluate(f"window.scrollTo(0, {current_y})")
                            page.wait_for_timeout(500)
                            
                            raw_elements = extract_elements(page)
                            
                            # なぜ: 新規要素と重複要素の数をそれぞれカウントして分析しやすくするため
                            new_count = 0
                            duplicate_count = 0
                            
                            for el in raw_elements:
                                theme_hash = f"{theme}|{el['hash']}"
                                if theme_hash not in seen_element_hashes:
                                    new_count += 1
                                    seen_element_hashes.add(theme_hash)
                                else:
                                    duplicate_count += 1
                            
                            # なぜ: その画面に1つでも新規要素があれば保存を実行する
                            if new_count > 0:
                                timestamp = int(time.time() * 1000)
                                base_filename = f"scraped_{timestamp}_{theme}_{page_count:05d}_{screen_index:02d}"
                                img_path = os.path.join(OUTPUT_IMG_DIR, f"{base_filename}.jpg")
                                lbl_path = os.path.join(OUTPUT_LBL_DIR, f"{base_filename}.txt")
                                
                                page.screenshot(path=img_path, type="jpeg", quality=90, full_page=False)
                                
                                with open(lbl_path, "w", encoding="utf-8") as f:
                                    for el in raw_elements:
                                        f.write(f"{el['class_id']} {el['x']:.6f} {el['y']:.6f} {el['w']:.6f} {el['h']:.6f}\n")
                                        
                                print(f"  -> [{theme} 領域{screen_index}] 計 {len(raw_elements)} 個の要素を抽出 (新規: {new_count} / 重複: {duplicate_count})")
                            
                            restore_hidden_elements(page)
                            
                            overlap = 200
                            current_y += (VIEWPORT_HEIGHT - overlap)
                            screen_index += 1
                            
                            if screen_index > 50:
                                break

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
                url_manager.mark_as_visited(current_url)

        browser.close()
        print(f"\n完了: {start_url} から監視ループへ移行します。")
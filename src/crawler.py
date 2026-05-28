# AI-ROLE: ページ遷移、スクロール、スクリーンショット保存などのブラウザ操作を統括するモジュール(非同期版)
import os
import time
from urllib.parse import urljoin, urlparse
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from src.config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, OUTPUT_IMG_DIR, OUTPUT_LBL_DIR, TIMEOUT_MS, MAX_RETRIES
from src.extractor import extract_elements, restore_hidden_elements
from src.url_manager import UrlManager
from src.balancer import DatasetBalancer

async def crawl_site(start_url: str, url_manager: UrlManager, context):
    queue = [start_url]
    seen_element_hashes = set() 
    
    # なぜ: 別のサイトでの取得割合が現在のサイトの収集に影響(過剰なスキップ等)を与えないようにするため、ドメインごとにバランサーをリセットする
    balancer = DatasetBalancer()

    page = await context.new_page()
    page.set_default_timeout(TIMEOUT_MS)

    while queue:
        current_url = queue.pop(0)
        
        if url_manager.is_visited(current_url):
            continue
            
        if not url_manager.can_visit_domain(current_url):
            domain = urlparse(current_url).netloc
            print(f"[Worker] スキップ: {domain} はドメインごとの収集上限に達しました")
            continue
            
        print(f"[Worker] 処理中: {current_url}")
        
        success = False
        for attempt in range(MAX_RETRIES):
            try:
                await page.goto(current_url, wait_until="networkidle")
                
                await page.evaluate("""() => {
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
                await page.wait_for_timeout(1000)
                
                await page.add_style_tag(content="::-webkit-scrollbar { display: none !important; } * { scrollbar-width: none !important; }")
                
                total_height = await page.evaluate("document.body.scrollHeight")
                if total_height == 0:
                    total_height = VIEWPORT_HEIGHT
                
                for theme in ["light", "dark"]:
                    await page.emulate_media(color_scheme=theme)
                    await page.evaluate(f"""(currentTheme) => {{
                        if (currentTheme === 'dark') {{
                            document.documentElement.classList.add('dark');
                            document.documentElement.setAttribute('data-theme', 'dark');
                        }} else {{
                            document.documentElement.classList.remove('dark');
                            document.documentElement.setAttribute('data-theme', 'light');
                        }}
                    }}""", theme)
                    await page.wait_for_timeout(1000)
                    
                    current_y = 0
                    screen_index = 0
                    
                    while current_y < total_height:
                        await page.evaluate(f"window.scrollTo(0, {current_y})")
                        await page.wait_for_timeout(500)
                        
                        raw_elements = await extract_elements(page)
                        has_new_in_site = False
                        
                        for el in raw_elements:
                            if el['hash'] not in seen_element_hashes:
                                has_new_in_site = True
                                seen_element_hashes.add(el['hash'])
                        
                        if has_new_in_site:
                            # サイトごとのバランサーに問い合わせ
                            if balancer.should_keep(raw_elements):
                                timestamp = int(time.time() * 1000)
                                base_filename = f"scraped_{timestamp}_{theme}_{screen_index:02d}"
                                img_path = os.path.join(OUTPUT_IMG_DIR, f"{base_filename}.jpg")
                                lbl_path = os.path.join(OUTPUT_LBL_DIR, f"{base_filename}.txt")
                                
                                await page.screenshot(path=img_path, type="jpeg", quality=90, full_page=False)
                                
                                with open(lbl_path, "w", encoding="utf-8") as f:
                                    for el in raw_elements:
                                        f.write(f"{el['class_id']} {el['x']:.6f} {el['y']:.6f} {el['w']:.6f} {el['h']:.6f}\n")
                                
                                balancer.register(raw_elements)
                                print(f"  -> [{theme} 領域{screen_index}] 保存完了 ({len(raw_elements)}要素) | サイト内統計: {balancer.get_stats()}")
                            else:
                                print(f"  -> [{theme} 領域{screen_index}] スキップ: このサイト内で既に十分に収集済みの要素ばかりです")
                        
                        await restore_hidden_elements(page)
                        
                        overlap = 200
                        current_y += (VIEWPORT_HEIGHT - overlap)
                        screen_index += 1
                        
                        if screen_index > 50:
                            break

                url_manager.mark_as_visited(current_url)
                
                if url_manager.can_visit_domain(start_url):
                    hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
                    for href in hrefs:
                        full_url = urljoin(current_url, href)
                        if url_manager.is_valid_url(start_url, full_url) and not url_manager.is_visited(full_url):
                            queue.append(full_url)
                else:
                    print(f"[Worker] {urlparse(start_url).netloc} のドメイン上限到達により、内部リンクの追跡を停止します")
                    queue.clear()
                        
                success = True
                break 
            except PlaywrightTimeoutError:
                print(f"  -> [警告] タイムアウト (試行 {attempt + 1}/{MAX_RETRIES}): {current_url}")
            except Exception as e:
                print(f"  -> [エラー] 例外発生 (試行 {attempt + 1}/{MAX_RETRIES}): {e}")
                
        if not success:
            print(f"  -> [失敗] {MAX_RETRIES}回の試行に失敗しました: {current_url}")
            url_manager.mark_as_visited(current_url)

    await page.close()
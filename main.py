# AI-ROLE: Webサイトを自動巡回(クローリング)し、複数のUI要素のYOLO形式データセットを生成するクローラー
import os
import time
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# YOLOのクラス定義
CLASSES = {
    "button": 0,
    "input": 1,
    "image": 2
}

OUTPUT_IMG_DIR = "datasets/auto_scraped/images/train"
OUTPUT_LBL_DIR = "datasets/auto_scraped/labels/train"
os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
os.makedirs(OUTPUT_LBL_DIR, exist_ok=True)

def is_valid_url(base_url, target_url):
    # なぜ: 外部サイトへの無限の巡回や、PDF/画像への直接リンクを除外するため
    base_domain = urlparse(base_url).netloc
    target_parsed = urlparse(target_url)
    
    if target_parsed.netloc != base_domain:
        return False
    if target_url.lower().endswith(('.pdf', '.png', '.jpg', '.zip')):
        return False
    return target_parsed.scheme in ['http', 'https']

def extract_elements(page, viewport_width, viewport_height):
    # なぜ: JS側で各要素をカテゴリ分けし、YOLOのクラスIDとともに座標を返すため
    return page.evaluate(f"""() => {{
        const data = [];
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.left >= 0) {{
                // YOLO正規化座標の計算
                const x_center = (rect.x + rect.width / 2) / {viewport_width};
                const y_center = (rect.y + rect.height / 2) / {viewport_height};
                const width = rect.width / {viewport_width};
                const height = rect.height / {viewport_height};
                data.push({{ class_id: classId, x: x_center, y: y_center, w: width, h: height }});
            }}
        }};

        // 0: Button
        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"]').forEach(el => pushRect(el, {CLASSES['button']}));
        
        // 1: Input (テキストボックスやセレクトボックス)
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]), textarea, select').forEach(el => pushRect(el, {CLASSES['input']}));
        
        // 2: Image
        document.querySelectorAll('img, svg').forEach(el => pushRect(el, {CLASSES['image']}));

        return data;
    }}""")

def crawl_and_scrape(start_url, max_pages=50):
    visited_urls = set()
    queue = [start_url]
    
    viewport_width = 1280
    viewport_height = 720

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page(viewport={"width": viewport_width, "height": viewport_height})
        page.set_default_timeout(15000) # なぜ: 外部通信のハングアップを防ぐため15秒でタイムアウト

        page_count = 0

        while queue and page_count < max_pages:
            current_url = queue.pop(0)
            
            # URLのフラグメント(#)を削除して重複判定
            clean_url = current_url.split('#')[0]
            if clean_url in visited_urls:
                continue
                
            visited_urls.add(clean_url)
            page_count += 1
            
            print(f"[{page_count}/{max_pages}] 処理中: {clean_url}")

            try:
                page.goto(clean_url, wait_until="networkidle")
                page.evaluate("document.body.style.overflow = 'hidden';")
                time.sleep(1) # なぜ: アニメーションや遅延レンダリングを待つため
                
                # 画像の保存
                img_path = os.path.join(OUTPUT_IMG_DIR, f"scraped_{page_count:05d}.jpg")
                page.screenshot(path=img_path, type="jpeg", quality=90)

                # 要素の抽出とラベル保存
                elements = extract_elements(page, viewport_width, viewport_height)
                lbl_path = os.path.join(OUTPUT_LBL_DIR, f"scraped_{page_count:05d}.txt")
                
                with open(lbl_path, "w", encoding="utf-8") as f:
                    for el in elements:
                        f.write(f"{el['class_id']} {el['x']:.6f} {el['y']:.6f} {el['w']:.6f} {el['h']:.6f}\n")

                print(f"  -> {len(elements)} 個の要素を抽出しました。")

                # 次のリンクを抽出してキューに追加
                hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
                for href in hrefs:
                    full_url = urljoin(clean_url, href)
                    if is_valid_url(start_url, full_url) and full_url.split('#')[0] not in visited_urls:
                        queue.append(full_url)

            except PlaywrightTimeoutError:
                print(f"  -> [警告] タイムアウト: {clean_url}")
            except Exception as e:
                print(f"  -> [エラー] 予期せぬ例外: {e}")

        browser.close()
        print(f"\n完了: 合計 {page_count} ページを処理しました。")

if __name__ == "__main__":
    # 出発点となるURLを指定
    START_URL = "https://example.com" 
    # なぜ: サーバー負荷とデータ肥大化を防ぐための上限
    MAX_PAGES_TO_SCRAPE = 100 
    
    crawl_and_scrape(START_URL, max_pages=MAX_PAGES_TO_SCRAPE)
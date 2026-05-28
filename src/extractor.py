# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES

def extract_elements(page):
    # なぜ: 画面に完全に入っている要素のみを抽出し、見切れている要素は画像から消去して誤学習を防ぐため
    return page.evaluate(f"""() => {{
        const data = [];
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            
            // 画面内に「少しでも」入っているか判定
            if (rect.bottom > 0 && rect.right > 0 && rect.top < vh && rect.left < vw) {{
                
                // 完全に見えているか判定 (1pxの余裕を持たせて丸め誤差を吸収)
                const isFullyVisible = rect.top >= -1 && rect.left >= -1 && rect.bottom <= vh + 1 && rect.right <= vw + 1;

                if (isFullyVisible) {{
                    const x_center = (rect.left + rect.width / 2) / vw;
                    const y_center = (rect.top + rect.height / 2) / vh;
                    const w = rect.width / vw;
                    const h = rect.height / vh;
                    
                    const tag = el.tagName || '';
                    const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
                    const text = (el.textContent || '').trim().substring(0, 50);
                    const src = el.src || '';
                    const type = el.type || '';
                    const origW = Math.round(rect.width);
                    const origH = Math.round(rect.height);
                    const elementHash = `${{tag}}|${{classes}}|${{origW}}x${{origH}}|${{text}}|${{src}}|${{type}}`;

                    data.push({{ 
                        class_id: classId, 
                        x: x_center, 
                        y: y_center, 
                        w: w, 
                        h: h,
                        hash: elementHash
                    }});
                }} else {{
                    // なぜ: 見切れている要素が画像に写り込み、背景として誤学習されるのを防ぐため透明化する
                    el.setAttribute('data-scraper-hidden', el.style.opacity || 'none');
                    el.style.opacity = '0';
                }}
            }}
        }};

        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"], input[type="reset"]').forEach(el => pushRect(el, {CLASSES['button']}));
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]):not([type="radio"]):not([type="checkbox"]):not([type="range"]):not([type="reset"]), textarea').forEach(el => pushRect(el, {CLASSES['text_input']}));
        document.querySelectorAll('input[type="checkbox"], [role="checkbox"]').forEach(el => pushRect(el, {CLASSES['checkbox']}));
        document.querySelectorAll('input[type="radio"], [role="radio"]').forEach(el => pushRect(el, {CLASSES['radio']}));
        document.querySelectorAll('select, [role="combobox"], [role="listbox"]').forEach(el => pushRect(el, {CLASSES['select']}));
        document.querySelectorAll('input[type="range"], [role="slider"]').forEach(el => pushRect(el, {CLASSES['slider']}));
        document.querySelectorAll('[role="switch"]').forEach(el => pushRect(el, {CLASSES['switch']}));
        document.querySelectorAll('img:not([class*="logo" i])').forEach(el => pushRect(el, {CLASSES['image']}));
        
        document.querySelectorAll('header svg, header img, [class*="logo" i]').forEach(el => {{
            if (el.tagName.toLowerCase() === 'svg' || el.tagName.toLowerCase() === 'img') {{
                pushRect(el, {CLASSES['logo']});
            }}
        }});
        
        document.querySelectorAll('svg').forEach(el => {{
            const closestHeader = el.closest('header');
            const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
            if (!closestHeader && !classes.toLowerCase().includes('logo')) {{
                pushRect(el, {CLASSES['icon']});
            }}
        }});
        
        document.querySelectorAll('a[href]:not(.btn):not([role="button"])').forEach(el => pushRect(el, {CLASSES['link']}));

        return data;
    }}""")

def restore_hidden_elements(page):
    # なぜ: 次の画面スクロール処理に影響を与えないよう、透明化した要素を元の状態に復元するため
    page.evaluate("""() => {
        document.querySelectorAll('[data-scraper-hidden]').forEach(el => {
            const originalOpacity = el.getAttribute('data-scraper-hidden');
            if (originalOpacity === 'none') {
                el.style.opacity = '';
            } else {
                el.style.opacity = originalOpacity;
            }
            el.removeAttribute('data-scraper-hidden');
        });
    }""")
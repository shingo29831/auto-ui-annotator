# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES

def extract_elements(page):
    # なぜ: 画面分割方式に合わせて、現在のビューポート(画面)内にある要素のみをクリッピングしてYOLO座標を計算するため
    return page.evaluate(f"""() => {{
        const data = [];
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            
            // 現在のビューポート内に見えているか判定（完全に見切れているものは除外）
            if (rect.bottom > 0 && rect.right > 0 && rect.top < vh && rect.left < vw) {{
                
                // 画面外にはみ出している部分はクリッピング（切り落とし）する
                const visibleLeft = Math.max(0, rect.left);
                const visibleTop = Math.max(0, rect.top);
                const visibleRight = Math.min(vw, rect.right);
                const visibleBottom = Math.min(vh, rect.bottom);
                
                const visibleWidth = visibleRight - visibleLeft;
                const visibleHeight = visibleBottom - visibleTop;

                // あまりにも小さい見切れ要素(5px未満)はノイズになるため除外
                if (visibleWidth >= 5 && visibleHeight >= 5) {{
                    // YOLO正規化座標 (ビューポート相対座標)
                    const x_center = (visibleLeft + visibleWidth / 2) / vw;
                    const y_center = (visibleTop + visibleHeight / 2) / vh;
                    const w = visibleWidth / vw;
                    const h = visibleHeight / vh;
                    
                    const tag = el.tagName || '';
                    const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
                    const text = (el.textContent || '').trim().substring(0, 50);
                    const src = el.src || '';
                    const type = el.type || '';
                    // ハッシュ生成には元のサイズを使用（見切れによるハッシュ変化を防ぐため）
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
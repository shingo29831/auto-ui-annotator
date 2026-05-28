# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES

def extract_elements(page):
    # なぜ: 細分化されたUIクラスの座標を網羅的に抽出し、YOLO形式で返すため
    return page.evaluate(f"""() => {{
        const data = [];
        
        const pageWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
        const pageHeight = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
        
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {{
                const absoluteX = rect.x + window.scrollX;
                const absoluteY = rect.y + window.scrollY;
                
                const x_center = (absoluteX + rect.width / 2) / pageWidth;
                const y_center = (absoluteY + rect.height / 2) / pageHeight;
                const width = rect.width / pageWidth;
                const height = rect.height / pageHeight;
                
                const tag = el.tagName || '';
                // なぜ: SVG要素のclassNameはSVGAnimatedStringオブジェクトになる場合がありエラーを防ぐため
                const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
                const text = (el.textContent || '').trim().substring(0, 50);
                const src = el.src || '';
                const type = el.type || '';
                const w = Math.round(rect.width);
                const h = Math.round(rect.height);
                const elementHash = `${{tag}}|${{classes}}|${{w}}x${{h}}|${{text}}|${{src}}|${{type}}`;

                data.push({{ 
                    class_id: classId, 
                    x: x_center, 
                    y: y_center, 
                    w: width, 
                    h: height,
                    hash: elementHash
                }});
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
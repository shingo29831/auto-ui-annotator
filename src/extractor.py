# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES

def extract_elements(page):
    # なぜ: 拡張されたUIクラス(リンク、トグル、アイコン等)の座標を網羅的に抽出し、YOLO形式で返すため
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

        // 0: Button
        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"]').forEach(el => pushRect(el, {CLASSES['button']}));
        
        // 1: Input
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]):not([type="radio"]):not([type="checkbox"]), textarea, select').forEach(el => pushRect(el, {CLASSES['input']}));
        
        // 2: Image
        document.querySelectorAll('img:not([class*="logo" i])').forEach(el => pushRect(el, {CLASSES['image']}));
        
        // 3: Logo (なぜ: ヘッダー内の画像/SVG、またはクラス名にlogoを含むものをブランドロゴとして抽出するため)
        document.querySelectorAll('header svg, header img, [class*="logo" i]').forEach(el => {{
            if (el.tagName.toLowerCase() === 'svg' || el.tagName.toLowerCase() === 'img') {{
                pushRect(el, {CLASSES['logo']});
            }}
        }});
        
        // 4: Icon (なぜ: Logo以外の機能的なSVGアイコンをRPA操作対象として分離するため)
        document.querySelectorAll('svg').forEach(el => {{
            const closestHeader = el.closest('header');
            const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
            if (!closestHeader && !classes.toLowerCase().includes('logo')) {{
                pushRect(el, {CLASSES['icon']});
            }}
        }});
        
        // 5: Link (なぜ: ボタン形状ではないナビゲーション用のテキストリンクを抽出するため)
        document.querySelectorAll('a[href]:not(.btn):not([role="button"])').forEach(el => pushRect(el, {CLASSES['link']}));
        
        // 6: Toggle (なぜ: モダンSPAで多用されるaria-role実装のスイッチやラジオボタンを抽出するため)
        document.querySelectorAll('[role="switch"], [role="radio"], [role="checkbox"], input[type="radio"], input[type="checkbox"]').forEach(el => pushRect(el, {CLASSES['toggle']}));

        return data;
    }}""")
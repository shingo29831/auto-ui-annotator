# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES, VIEWPORT_WIDTH, VIEWPORT_HEIGHT

def extract_elements(page):
    # なぜ: JS側で各要素をカテゴリ分けし、YOLOのクラスIDと要素の一意なハッシュ、座標を返すため
    return page.evaluate(f"""() => {{
        const data = [];
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.left >= 0) {{
                const x_center = (rect.x + rect.width / 2) / {VIEWPORT_WIDTH};
                const y_center = (rect.y + rect.height / 2) / {VIEWPORT_HEIGHT};
                const width = rect.width / {VIEWPORT_WIDTH};
                const height = rect.height / {VIEWPORT_HEIGHT};
                
                // なぜ: 同一サイト内の全く同じUI(ヘッダーのボタンなど)を弾くためのハッシュ生成
                const tag = el.tagName || '';
                // SVGなどはclassNameがオブジェクトになる場合があるため型を検証
                const classes = typeof el.className === 'string' ? el.className : '';
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

        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"]').forEach(el => pushRect(el, {CLASSES['button']}));
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]), textarea, select').forEach(el => pushRect(el, {CLASSES['input']}));
        document.querySelectorAll('img, svg').forEach(el => pushRect(el, {CLASSES['image']}));

        return data;
    }}""")
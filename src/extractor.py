# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES

def extract_elements(page):
    # なぜ: JS側で各要素をカテゴリ分けし、ページ全体に対するYOLOのクラスIDと一意なハッシュ、座標を返すため
    return page.evaluate(f"""() => {{
        const data = [];
        
        // なぜ: フルページスクリーンショットの画像サイズとYOLO座標の分母を一致させるため
        const pageWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
        const pageHeight = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
        
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            // なぜ: スクロールで見切れている要素も取得するため top >= 0 などの条件を削除し、表示の有無のみ判定
            if (rect.width > 0 && rect.height > 0) {{
                // viewport相対座標からページ全体の絶対座標へ変換
                const absoluteX = rect.x + window.scrollX;
                const absoluteY = rect.y + window.scrollY;
                
                const x_center = (absoluteX + rect.width / 2) / pageWidth;
                const y_center = (absoluteY + rect.height / 2) / pageHeight;
                const width = rect.width / pageWidth;
                const height = rect.height / pageHeight;
                
                // なぜ: 同一サイト内の全く同じUI(ヘッダーのボタンなど)を弾くためのハッシュ生成
                const tag = el.tagName || '';
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
# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール
from src.config import CLASSES, VIEWPORT_WIDTH, VIEWPORT_HEIGHT

def extract_elements(page):
    # なぜ: JS側で各要素をカテゴリ分けし、YOLOのクラスIDとともに座標を返すため
    return page.evaluate(f"""() => {{
        const data = [];
        const pushRect = (el, classId) => {{
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.left >= 0) {{
                const x_center = (rect.x + rect.width / 2) / {VIEWPORT_WIDTH};
                const y_center = (rect.y + rect.height / 2) / {VIEWPORT_HEIGHT};
                const width = rect.width / {VIEWPORT_WIDTH};
                const height = rect.height / {VIEWPORT_HEIGHT};
                data.push({{ class_id: classId, x: x_center, y: y_center, w: width, h: height }});
            }}
        }};

        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"]').forEach(el => pushRect(el, {CLASSES['button']}));
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]), textarea, select').forEach(el => pushRect(el, {CLASSES['input']}));
        document.querySelectorAll('img, svg').forEach(el => pushRect(el, {CLASSES['image']}));

        return data;
    }}""")
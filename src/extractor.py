# AI-ROLE: ブラウザ上のDOMから指定されたUI要素の座標を抽出し、YOLO形式に変換するモジュール(非同期版)
from src.config import CLASSES

async def extract_elements(page):
    return await page.evaluate(f"""() => {{
        const data = [];
        const processedElements = new Set();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        
        const pushRect = (el, classId) => {{
            if (processedElements.has(el)) return;
            
            // なぜ: 画像上に実際に描画されない要素(display: none, visibility: hidden等)をデータセットから排除するため
            const computed = window.getComputedStyle(el);
            if (
                computed.display === 'none' ||
                computed.visibility === 'hidden' ||
                computed.opacity === '0' ||
                el.offsetWidth === 0 ||
                el.offsetHeight === 0
            ) {{
                return;
            }}
            
            const rect = el.getBoundingClientRect();
            if (rect.bottom > 0 && rect.right > 0 && rect.top < vh && rect.left < vw) {{
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

                    const quantizeColor = (colorStr) => {{
                        const match = colorStr.match(/\d+/g);
                        if (!match || match.length < 3) return 'transparent';
                        // なぜ: RGB成分を大まかに丸める(32刻み)ことで、わずかな色の違い(近しい色)を同一視し、大きく違う色をレア要素として分類するため
                        const r = Math.round(parseInt(match[0]) / 32) * 32;
                        const g = Math.round(parseInt(match[1]) / 32) * 32;
                        const b = Math.round(parseInt(match[2]) / 32) * 32;
                        return `${{r}},${{g}},${{b}}`;
                    }};
                    
                    const bgColor = quantizeColor(computed.backgroundColor);
                    const textColor = quantizeColor(computed.color);
                    // なぜ: 10pxの誤差などは「近しい形状」として同一視するため、サイズを20px単位で丸める
                    const approxW = Math.round(origW / 20) * 20;
                    const approxH = Math.round(origH / 20) * 20;
                    
                    const visualHash = `${{classId}}|${{bgColor}}|${{textColor}}|${{approxW}}x${{approxH}}`;

                    data.push({{ 
                        class_id: classId, 
                        x: x_center, 
                        y: y_center, 
                        w: w, 
                        h: h,
                        hash: elementHash,
                        visual_hash: visualHash 
                    }});
                    processedElements.add(el);
                }} else {{
                    el.setAttribute('data-scraper-hidden', el.style.opacity || 'none');
                    el.style.opacity = '0';
                }}
            }}
        }};

        document.querySelectorAll('dialog, [role="dialog"], [role="alertdialog"], [class*="modal" i]').forEach(el => pushRect(el, {CLASSES['modal']}));
        document.querySelectorAll('[role="alert"], [role="status"], [class*="toast" i], [class*="alert" i]').forEach(el => pushRect(el, {CLASSES['alert']}));
        document.querySelectorAll('[role="menu"], [class*="dropdown-menu" i]').forEach(el => pushRect(el, {CLASSES['dropdown']}));
        document.querySelectorAll('[role="tooltip"], [class*="tooltip" i], [class*="popover" i]').forEach(el => pushRect(el, {CLASSES['tooltip']}));
        document.querySelectorAll('details, [class*="accordion" i]').forEach(el => pushRect(el, {CLASSES['accordion']}));
        document.querySelectorAll('nav[aria-label*="breadcrumb" i], [class*="breadcrumb" i]').forEach(el => pushRect(el, {CLASSES['breadcrumb']}));
        document.querySelectorAll('nav[aria-label*="pagination" i], [class*="pagination" i]').forEach(el => pushRect(el, {CLASSES['pagination']}));
        document.querySelectorAll('[role="tab"], .tab, [class*="tab-" i]').forEach(el => pushRect(el, {CLASSES['tab']}));
        
        document.querySelectorAll('canvas, [class*="chart" i], [class*="graph" i]').forEach(el => pushRect(el, {CLASSES['chart']}));
        document.querySelectorAll('table, [role="grid"], [role="treegrid"]').forEach(el => pushRect(el, {CLASSES['table']}));
        document.querySelectorAll('progress, [role="progressbar"], [class*="spinner" i], [class*="loader" i]').forEach(el => pushRect(el, {CLASSES['spinner']}));
        document.querySelectorAll('[class*="badge" i]:not(body):not(div:empty), [class*="tag" i], [class*="chip" i]').forEach(el => pushRect(el, {CLASSES['badge']}));
        document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]').forEach(el => pushRect(el, {CLASSES['heading']}));
        
        document.querySelectorAll('input[type="date"], input[type="time"], input[type="datetime-local"], input[type="month"], input[type="week"]').forEach(el => pushRect(el, {CLASSES['datepicker']}));
        document.querySelectorAll('[role="switch"]').forEach(el => pushRect(el, {CLASSES['switch']}));
        document.querySelectorAll('input[type="checkbox"], [role="checkbox"]').forEach(el => pushRect(el, {CLASSES['checkbox']}));
        document.querySelectorAll('input[type="radio"], [role="radio"]').forEach(el => pushRect(el, {CLASSES['radio']}));
        document.querySelectorAll('select, [role="combobox"], [role="listbox"]').forEach(el => pushRect(el, {CLASSES['select']}));
        document.querySelectorAll('input[type="range"], [role="slider"]').forEach(el => pushRect(el, {CLASSES['slider']}));
        document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]):not([type="radio"]):not([type="checkbox"]):not([type="range"]):not([type="reset"]):not([type="date"]):not([type="time"]):not([type="datetime-local"]):not([type="month"]):not([type="week"]), textarea').forEach(el => pushRect(el, {CLASSES['text_input']}));
        
        document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"], input[type="reset"]').forEach(el => pushRect(el, {CLASSES['button']}));
        document.querySelectorAll('a[href]:not(.btn):not([role="button"])').forEach(el => pushRect(el, {CLASSES['link']}));
        
        document.querySelectorAll('img[class*="avatar" i], [class*="avatar" i]').forEach(el => pushRect(el, {CLASSES['avatar']}));
        document.querySelectorAll('video, [class*="video" i]').forEach(el => pushRect(el, {CLASSES['video']}));
        document.querySelectorAll('iframe').forEach(el => pushRect(el, {CLASSES['iframe']}));
        document.querySelectorAll('header svg, header img, [class*="logo" i]').forEach(el => {{
            if (el.tagName.toLowerCase() === 'svg' || el.tagName.toLowerCase() === 'img') {{
                pushRect(el, {CLASSES['logo']});
            }}
        }});
        document.querySelectorAll('img:not([class*="logo" i]):not([class*="avatar" i])').forEach(el => pushRect(el, {CLASSES['image']}));
        document.querySelectorAll('svg').forEach(el => {{
            const closestHeader = el.closest('header');
            const classes = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
            if (!closestHeader && !classes.toLowerCase().includes('logo') && !classes.toLowerCase().includes('avatar')) {{
                pushRect(el, {CLASSES['icon']});
            }}
        }});

        return data;
    }}""")

async def restore_hidden_elements(page):
    await page.evaluate("""() => {
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
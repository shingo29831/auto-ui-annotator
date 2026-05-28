# AI-ROLE: プロジェクト全体の設定値やパスを管理する設定ファイル
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OUTPUT_IMG_DIR = os.getenv('OUTPUT_IMG_DIR', 'datasets/auto_scraped/images/train')
OUTPUT_LBL_DIR = os.getenv('OUTPUT_LBL_DIR', 'datasets/auto_scraped/labels/train')
TARGET_URLS_FILE = "target_urls.txt"
VISITED_URLS_FILE = "visited_urls.txt"

MAX_PAGES_TO_SCRAPE = 100
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
TIMEOUT_MS = 15000
MAX_RETRIES = 3

# なぜ: 形状が異なる要素を同じクラスに混ぜるとYOLOの精度が下がるため、タイプ別に細分化して定義
CLASSES = {
    "button": 0,
    "text_input": 1,
    "checkbox": 2,
    "radio": 3,
    "select": 4,
    "slider": 5,
    "switch": 6,
    "image": 7,
    "logo": 8,
    "icon": 9,
    "link": 10
}

os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
os.makedirs(OUTPUT_LBL_DIR, exist_ok=True)

if not os.path.exists(VISITED_URLS_FILE):
    open(VISITED_URLS_FILE, 'w', encoding="utf-8").close()
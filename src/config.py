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

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
TIMEOUT_MS = 15000
MAX_RETRIES = 3

MAX_CONCURRENT_SITES = int(os.getenv('MAX_CONCURRENT_SITES', 3))
BALANCER_TARGET_LIMIT = int(os.getenv('BALANCER_TARGET_LIMIT', 5000))

# なぜ: 同一サイトからの過剰な収集を防ぎ「浅く広く」学習させるため、ドメインごとのページ上限を絞る
MAX_PAGES_PER_DOMAIN = int(os.getenv('MAX_PAGES_PER_DOMAIN', 10))

CLASSES = {
    "button": 0, "text_input": 1, "checkbox": 2, "radio": 3, 
    "select": 4, "slider": 5, "switch": 6, "image": 7, 
    "logo": 8, "icon": 9, "link": 10, "tab": 11, 
    "table": 12, "spinner": 13, "badge": 14, "heading": 15, 
    "modal": 16, "tooltip": 17, "breadcrumb": 18, "pagination": 19, 
    "video": 20, "iframe": 21, "datepicker": 22, "alert": 23, 
    "accordion": 24, "dropdown": 25, "avatar": 26, "chart": 27
}

os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
os.makedirs(OUTPUT_LBL_DIR, exist_ok=True)

if not os.path.exists(VISITED_URLS_FILE):
    open(VISITED_URLS_FILE, 'w', encoding="utf-8").close()
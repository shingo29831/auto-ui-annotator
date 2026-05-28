# AI-ROLE: プロジェクト全体の設定値やパスを管理する設定ファイル
import os

# なぜ: 環境変数ファイル(.env)が存在する場合に自動で読み込むため
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# なぜ: SSD容量圧迫を防ぐため、環境変数から保存先パスを取得する(未指定時はデフォルト値)
OUTPUT_IMG_DIR = os.getenv('OUTPUT_IMG_DIR', 'datasets/auto_scraped/images/train')
OUTPUT_LBL_DIR = os.getenv('OUTPUT_LBL_DIR', 'datasets/auto_scraped/labels/train')
TARGET_URLS_FILE = "target_urls.txt"
VISITED_URLS_FILE = "visited_urls.txt"

MAX_PAGES_TO_SCRAPE = 100
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
TIMEOUT_MS = 15000
MAX_RETRIES = 3

CLASSES = {
    "button": 0,
    "input": 1,
    "image": 2
}

os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
os.makedirs(OUTPUT_LBL_DIR, exist_ok=True)

if not os.path.exists(VISITED_URLS_FILE):
    # なぜ: Windows環境での文字化けやプラットフォーム依存のバグを防ぐため
    open(VISITED_URLS_FILE, 'w', encoding="utf-8").close()
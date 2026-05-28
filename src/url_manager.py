# AI-ROLE: 対象URLの読み込み、訪問済みURLの管理、URLの妥当性検証を担うモジュール
import os
from urllib.parse import urlparse

class UrlManager:
    def __init__(self, target_file: str, visited_file: str):
        self.target_file = target_file
        self.visited_file = visited_file
        self.visited_urls = self._load_visited_urls()
        
    def _load_visited_urls(self) -> set:
        if not os.path.exists(self.visited_file):
            return set()
        with open(self.visited_file, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
            
    def load_target_urls(self) -> list:
        if not os.path.exists(self.target_file):
            return []
        with open(self.target_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
            
    def is_visited(self, url: str) -> bool:
        clean_url = url.split('#')[0]
        return clean_url in self.visited_urls
        
    def mark_as_visited(self, url: str):
        clean_url = url.split('#')[0]
        if clean_url not in self.visited_urls:
            self.visited_urls.add(clean_url)
            with open(self.visited_file, "a", encoding="utf-8") as f:
                f.write(f"{clean_url}\n")
                
    def is_valid_url(self, base_url: str, target_url: str) -> bool:
        # なぜ: 外部サイトへの無限の巡回や、PDF/画像への直接リンクを除外するため
        base_domain = urlparse(base_url).netloc
        target_parsed = urlparse(target_url)
        
        if target_parsed.netloc != base_domain:
            return False
        if target_url.lower().endswith(('.pdf', '.png', '.jpg', '.zip')):
            return False
        return target_parsed.scheme in ['http', 'https']
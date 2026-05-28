# AI-ROLE: 対象URLの読み込み、訪問済みURLの管理、URLの妥当性とドメインごとの上限検証を担うモジュール
import os
from urllib.parse import urlparse

class UrlManager:
    def __init__(self, target_file: str, visited_file: str, max_per_domain: int):
        self.target_file = target_file
        self.visited_file = visited_file
        self.max_per_domain = max_per_domain
        self.visited_urls = set()
        self.domain_counts = {}
        self._load_visited_urls()
        
    def _load_visited_urls(self):
        if not os.path.exists(self.visited_file):
            return
        with open(self.visited_file, "r", encoding="utf-8") as f:
            for line in f:
                clean_url = line.strip()
                if clean_url:
                    self.visited_urls.add(clean_url)
                    # なぜ: スクリプト再起動時も過去に収集したドメインの比率を維持して過学習を防ぐため
                    domain = urlparse(clean_url).netloc
                    self.domain_counts[domain] = self.domain_counts.get(domain, 0) + 1
            
    def load_target_urls(self) -> list:
        if not os.path.exists(self.target_file):
            return []
        with open(self.target_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
            
    def is_visited(self, url: str) -> bool:
        clean_url = url.split('#')[0]
        return clean_url in self.visited_urls

    def can_visit_domain(self, url: str) -> bool:
        # なぜ: 特定のサイトのUIデザインばかりを過剰に学習するのを防ぐため、ドメインごとの上限をチェックする
        domain = urlparse(url).netloc
        return self.domain_counts.get(domain, 0) < self.max_per_domain
        
    def mark_as_visited(self, url: str):
        clean_url = url.split('#')[0]
        if clean_url not in self.visited_urls:
            self.visited_urls.add(clean_url)
            domain = urlparse(clean_url).netloc
            self.domain_counts[domain] = self.domain_counts.get(domain, 0) + 1
            
            with open(self.visited_file, "a", encoding="utf-8") as f:
                f.write(f"{clean_url}\n")
                
    def is_valid_url(self, base_url: str, target_url: str) -> bool:
        base_domain = urlparse(base_url).netloc
        target_parsed = urlparse(target_url)
        
        if target_parsed.netloc != base_domain:
            return False
        if target_url.lower().endswith(('.pdf', '.png', '.jpg', '.zip')):
            return False
        return target_parsed.scheme in ['http', 'https']
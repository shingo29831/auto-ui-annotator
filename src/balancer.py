# AI-ROLE: データセット全体のクラス分布を動的に監視し、希少要素の積極的収集と頻出要素の過学習防止を担うモジュール
from src.config import CLASSES

class DatasetBalancer:
    def __init__(self):
        self.counts = {class_id: 0 for class_id in CLASSES.values()}
        self.total_elements = 0

    def should_keep(self, elements: list) -> bool:
        if not elements:
            return False
            
        # なぜ: 学習初期段階は分布の基準となるデータ自体が不足しているため無条件で収集して統計の基礎を作る
        if self.total_elements < 1000:
            return True

        total_in_page = len(elements)
        avg_count = self.total_elements / len(self.counts)
        
        # なぜ: クラスごとの取得数の相対的な割合から「希少(レア)」と「頻出(コモン)」のボーダーラインを動的に決定するため
        rare_threshold = avg_count * 0.5
        common_threshold = avg_count * 1.5

        rare_count = 0
        common_count = 0

        for el in elements:
            current = self.counts[el['class_id']]
            if current < rare_threshold:
                rare_count += 1
            elif current > common_threshold:
                common_count += 1

        # なぜ: 割合として少ないUI(カレンダーやチャート等)が含まれるページは、全体のバランスを整えるため最優先で保存する
        if rare_count > 0:
            return True
            
        # なぜ: 希少な要素が一切なく、ボタンやリンク等の超頻出要素ばかりで構成された画面を弾いて過学習とストレージ圧迫を防ぐため
        if (common_count / total_in_page) > 0.8:
            return False
            
        return True

    def register(self, elements: list):
        for el in elements:
            self.counts[el['class_id']] += 1
            self.total_elements += 1

    def get_stats(self) -> str:
        # なぜ: ログ上で現在の「最も多いクラス」と「最も少ないクラス」の差を可視化し、バランサーの稼働状況を確認しやすくするため
        sorted_counts = sorted(self.counts.items(), key=lambda x: x[1])
        rarest = f"Min(ID{sorted_counts[0][0]}:{sorted_counts[0][1]})"
        most_common = f"Max(ID{sorted_counts[-1][0]}:{sorted_counts[-1][1]})"
        total = f"Total:{self.total_elements}"
        return f"{total} | {rarest} | {most_common}"
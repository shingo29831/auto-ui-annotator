# AI-ROLE: サイト(ドメイン)ごとのデータセットのクラス分布を動的に監視し、希少要素の積極的収集と頻出要素の過学習防止を担うモジュール
from src.config import CLASSES

class DatasetBalancer:
    def __init__(self):
        self.counts = {class_id: 0 for class_id in CLASSES.values()}
        self.total_elements = 0

    def should_keep(self, elements: list) -> bool:
        if not elements:
            return False
            
        # なぜ: サイト単位での評価となるため、閾値を大幅に下げて「最初の1〜2画面分」だけをサイト内統計の基礎として無条件収集する
        if self.total_elements < 150:
            return True

        total_in_page = len(elements)
        avg_count = self.total_elements / len(self.counts)
        
        # なぜ: 学習初期に平均値が低すぎることで生じる誤判定を防ぐため、平均値の最低ラインを設定
        if avg_count < 5:
            avg_count = 5
            
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

        # そのサイト内において希少な要素が1つでもあれば保存
        if rare_count > 0:
            return True
            
        # そのサイト内において超頻出要素(ヘッダーのリンクなど)が画面の80%以上を占める場合はスキップ
        if (common_count / total_in_page) > 0.8:
            return False
            
        return True

    def register(self, elements: list):
        for el in elements:
            self.counts[el['class_id']] += 1
            self.total_elements += 1

    def get_stats(self) -> str:
        sorted_counts = sorted(self.counts.items(), key=lambda x: x[1])
        rarest = f"Min(ID{sorted_counts[0][0]}:{sorted_counts[0][1]})"
        most_common = f"Max(ID{sorted_counts[-1][0]}:{sorted_counts[-1][1]})"
        total = f"Total:{self.total_elements}"
        return f"{total} | {rarest} | {most_common}"
# AI-ROLE: データセット全体の多様性（視覚的特徴）と、ドメインごとのクラス分布を管理し、取得判定を行うモジュール
from src.config import CLASSES

class DatasetBalancer:
    def __init__(self, global_visual_counts: dict):
        self.global_visual_counts = global_visual_counts
        self.domain_class_counts = {class_id: 0 for class_id in CLASSES.values()}
        self.domain_total_elements = 0

    def should_keep(self, elements: list) -> bool:
        if not elements:
            return False
            
        if self.domain_total_elements < 150:
            return True

        total_in_page = len(elements)
        avg_count = self.domain_total_elements / len(CLASSES)
        if avg_count < 5:
            avg_count = 5
            
        rare_threshold = avg_count * 0.5
        common_threshold = avg_count * 1.5

        rare_count = 0
        common_count = 0

        for el in elements:
            # 視覚的新規性チェック (グローバル辞書を参照)
            v_hash = el.get('visual_hash', '')
            if self.global_visual_counts.get(v_hash, 0) < 5:
                return True

            current = self.domain_class_counts[el['class_id']]
            if current < rare_threshold:
                rare_count += 1
            elif current > common_threshold:
                common_count += 1

        if rare_count > 0:
            return True
            
        if (common_count / total_in_page) > 0.8:
            return False
            
        return True

    def register(self, elements: list):
        for el in elements:
            self.domain_class_counts[el['class_id']] += 1
            self.domain_total_elements += 1
            
            v_hash = el.get('visual_hash', '')
            self.global_visual_counts[v_hash] = self.global_visual_counts.get(v_hash, 0) + 1

    def get_stats(self) -> str:
        sorted_counts = sorted(self.domain_class_counts.items(), key=lambda x: x[1])
        rarest = f"Min(ID{sorted_counts[0][0]}:{sorted_counts[0][1]})"
        most_common = f"Max(ID{sorted_counts[-1][0]}:{sorted_counts[-1][1]})"
        total = f"DomainTotal:{self.domain_total_elements}"
        return f"{total} | {rarest} | {most_common}"
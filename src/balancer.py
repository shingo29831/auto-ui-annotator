# AI-ROLE: データセット全体のクラスごとの偏りを監視し、過学習を防ぐための取得判定を行うモジュール
from src.config import CLASSES

class DatasetBalancer:
    def __init__(self, target_limit: int):
        self.target_limit = target_limit
        # クラスIDをキーにして取得件数をトラッキング
        self.counts = {class_id: 0 for class_id in CLASSES.values()}

    def should_keep(self, elements: list) -> bool:
        # なぜ: 希少な要素を含む画面のみを抽出し、頻出要素だけの画面をスキップしてデータ不均衡を防ぐため
        for el in elements:
            if self.counts[el['class_id']] < self.target_limit:
                return True
        return False

    def register(self, elements: list):
        # なぜ: 保存が確定した要素群のカウントを更新し、次回以降の動的判定にリアルタイムに反映させるため
        for el in elements:
            self.counts[el['class_id']] += 1

    def get_stats(self) -> str:
        # ログ表示用の簡易統計フォーマット
        return " / ".join([f"ID{k}:{v}" for k, v in list(self.counts.items())[:5]]) + " ..."
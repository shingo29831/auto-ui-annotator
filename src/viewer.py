# AI-ROLE: 収集した画像とアノテーションデータを重畳表示し、スクレイピング中のリアルタイム監視も可能なビューアモジュール
import os
import glob
from typing import List, Dict
from tkinter import Tk, Canvas, Label, Frame, BooleanVar, Checkbutton
from PIL import Image, ImageDraw, ImageTk
from src.config import CLASSES, OUTPUT_IMG_DIR, OUTPUT_LBL_DIR

class DatasetLoader:
    def __init__(self, img_dir: str, lbl_dir: str):
        self.img_dir = img_dir
        self.lbl_dir = lbl_dir
        self.class_map = {v: k for k, v in CLASSES.items()}
        self.image_files = []

    def refresh_files(self) -> int:
        if not os.path.isdir(self.img_dir):
            return 0
        
        supported_exts = ('*.jpg', '*.jpeg', '*.png')
        files = []
        for ext in supported_exts:
            files.extend(glob.glob(os.path.join(self.img_dir, ext)))
        
        # なぜ: スライダーや最新順での追従を正確に行うため、ファイル名（タイムスタンプ依存）でソートして状態を更新する
        self.image_files = sorted(files)
        return len(self.image_files)

    def get_image_files(self) -> List[str]:
        return self.image_files

    def load_labels(self, img_path: str, img_width: int, img_height: int) -> List[Dict]:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        lbl_path = os.path.join(self.lbl_dir, f"{base_name}.txt")
        
        if not os.path.isfile(lbl_path):
            return []

        annotations = []
        with open(lbl_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) != 5:
                    continue
                
                try:
                    class_id = int(parts[0])
                    x_c, y_c, w, h = map(float, parts[1:])
                except ValueError as e:
                    raise ValueError(f"Invalid label format in {lbl_path}: {line}") from e

                # なぜ: YOLO形式(中心座標と幅・高さの割合)から、Pillowで描画するための絶対ピクセル座標(左上と右下)に変換するため
                x1 = max(0, int((x_c - w / 2) * img_width))
                y1 = max(0, int((y_c - h / 2) * img_height))
                x2 = min(img_width, int((x_c + w / 2) * img_width))
                y2 = min(img_height, int((y_c + h / 2) * img_height))
                
                label_name = self.class_map.get(class_id, f"Unknown({class_id})")
                annotations.append({
                    'class_id': class_id,
                    'label': label_name,
                    'bbox': (x1, y1, x2, y2)
                })
        return annotations

class AnnotationViewer:
    def __init__(self, loader: DatasetLoader, interval_ms: int = 2000):
        self.loader = loader
        self.interval_ms = interval_ms
        self.current_index = 0
        
        self.root = Tk()
        self.root.title("Auto UI Annotator - Live Verification Viewer")
        
        self.canvas = Canvas(self.root, width=1280, height=720, bg="black")
        self.canvas.pack(fill="both", expand=True)
        
        self.control_frame = Frame(self.root, bg="gray")
        self.control_frame.pack(side="bottom", fill="x")
        
        self.live_mode = BooleanVar(value=True)
        self.live_check = Checkbutton(
            self.control_frame, 
            text="Live Mode (最新を自動追従)", 
            variable=self.live_mode, 
            bg="gray", 
            fg="white", 
            selectcolor="black",
            activebackground="gray",
            activeforeground="white"
        )
        self.live_check.pack(side="left", padx=10, pady=5)
        
        self.info_label = Label(self.control_frame, text="Starting...", font=("Arial", 12), bg="gray", fg="white")
        self.info_label.pack(side="left", fill="x", expand=True)
        
        self.photo_image = None
        
    def draw_annotations(self, img: Image.Image, annotations: List[Dict]) -> Image.Image:
        draw = ImageDraw.Draw(img)
        for ann in annotations:
            x1, y1, x2, y2 = ann['bbox']
            label = ann['label']
            
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            
            text_bbox = draw.textbbox((x1, y1), label)
            draw.rectangle([text_bbox[0], text_bbox[1], text_bbox[2], text_bbox[3]], fill="red")
            draw.text((x1, y1), label, fill="white")
            
        return img

    def show_next_image(self):
        total_files = self.loader.refresh_files()
        
        if total_files == 0:
            self.canvas.delete("all")
            self.canvas.create_text(640, 360, text="Waiting for scraper to save images...", fill="white", font=("Arial", 24))
            self.info_label.config(text="Directory is empty or not found. Monitoring...")
            self.root.after(self.interval_ms, self.show_next_image)
            return

        if self.live_mode.get():
            # なぜ: スクレイピングと並行実行した際に、常に一番新しく保存された画面を監視できるようにするため
            self.current_index = total_files - 1
        else:
            if self.current_index >= total_files:
                self.current_index = 0
                
        image_files = self.loader.get_image_files()
        img_path = image_files[self.current_index]
        
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            # なぜ: クローラーがファイル書き込み中のタイミングで読み込みアクセスするとクラッシュするため、次回サイクルでリトライする
            print(f"Warning: Image read blocked for {img_path}, retrying next tick: {e}")
            self.root.after(self.interval_ms, self.show_next_image)
            return

        try:
            annotations = self.loader.load_labels(img_path, img.width, img.height)
        except ValueError as e:
            # なぜ: ラベルファイルの書き込み途中に読み込んだ場合の不完全なデータエラーを検知し、次の監視サイクルで再取得するため
            print(f"Warning: Label read error for {img_path}, retrying next tick: {e}")
            self.root.after(self.interval_ms, self.show_next_image)
            return

        annotated_img = self.draw_annotations(img, annotations)
        annotated_img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
        
        self.photo_image = ImageTk.PhotoImage(annotated_img)
        self.canvas.delete("all")
        
        x_offset = (1280 - annotated_img.width) // 2
        y_offset = (720 - annotated_img.height) // 2
        self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.photo_image)
        
        mode_text = "[LIVE]" if self.live_mode.get() else "[SLIDESHOW]"
        self.info_label.config(text=f"{mode_text} Showing [{self.current_index + 1}/{total_files}]: {os.path.basename(img_path)} | Detected Elements: {len(annotations)}")
        
        if not self.live_mode.get():
            self.current_index += 1
            
        self.root.after(self.interval_ms, self.show_next_image)

    def start(self):
        self.show_next_image()
        self.root.mainloop()

if __name__ == "__main__":
    loader = DatasetLoader(OUTPUT_IMG_DIR, OUTPUT_LBL_DIR)
    # なぜ: リアルタイム監視のテンポを重視し、2秒(2000ms)間隔でポーリングを行う
    viewer = AnnotationViewer(loader, interval_ms=1000)
    viewer.start()
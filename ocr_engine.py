import os
import re
from typing import List, Dict, Any, Optional

class OCREngine:
    def __init__(self, languages: List[str] = None, use_gpu: bool = False):
        self.languages = languages or ['en']
        self.use_gpu = use_gpu
        self._easyocr_reader = None

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            import easyocr
            self._easyocr_reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
        return self._easyocr_reader

    def extract_text_easyocr(self, image_path: str) -> Dict[str, Any]:
        reader = self._get_easyocr_reader()
        # detail=1 returns list of (bbox, text, prob)
        results = reader.readtext(image_path)
        
        # Sort items vertically (top to bottom), then horizontally
        sorted_results = sorted(results, key=lambda x: (x[0][0][1], x[0][0][0]))
        
        lines = []
        full_text_parts = []
        
        for bbox, text, prob in sorted_results:
            text = text.strip()
            if not text:
                continue
            full_text_parts.append(text)
            lines.append({
                "text": text,
                "confidence": float(prob),
                "bbox": bbox
            })
            
        full_text = "\n".join(full_text_parts)
        
        return {
            "engine": "EasyOCR",
            "full_text": full_text,
            "lines": lines,
            "image_path": image_path
        }

    def extract_text_tesseract(self, image_path: str) -> Dict[str, Any]:
        import pytesseract
        from PIL import Image
        
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        lines = []
        full_text_parts = []
        n_boxes = len(data['text'])
        
        current_line_num = -1
        current_line_text = []
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if text and conf > 0:
                line_num = data['line_num'][i]
                if line_num != current_line_num:
                    if current_line_text:
                        line_str = " ".join(current_line_text)
                        full_text_parts.append(line_str)
                        lines.append({"text": line_str, "confidence": conf / 100.0})
                        current_line_text = []
                    current_line_num = line_num
                current_line_text.append(text)
                
        if current_line_text:
            line_str = " ".join(current_line_text)
            full_text_parts.append(line_str)
            lines.append({"text": line_str, "confidence": 0.9})
            
        full_text = "\n".join(full_text_parts)
        return {
            "engine": "Tesseract",
            "full_text": full_text,
            "lines": lines,
            "image_path": image_path
        }

    def extract(self, image_path: str, prefer: str = "easyocr") -> Dict[str, Any]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        if prefer.lower() == "tesseract":
            try:
                return self.extract_text_tesseract(image_path)
            except Exception:
                return self.extract_text_easyocr(image_path)
        else:
            try:
                return self.extract_text_easyocr(image_path)
            except Exception:
                return self.extract_text_tesseract(image_path)

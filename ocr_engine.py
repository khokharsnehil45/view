import os
import re
from typing import List, Dict, Any, Optional

class OCREngine:
    def __init__(self, languages: List[str] = None, use_gpu: bool = False):
        self.languages = languages or ['en']
        self.use_gpu = use_gpu
        self._rapidocr_engine = None
        self._easyocr_reader = None

    def _get_rapidocr_engine(self):
        """Ultra-fast, lightweight CPU ONNX engine based on PP-OCRv4."""
        if self._rapidocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._rapidocr_engine = RapidOCR()
        return self._rapidocr_engine

    def _get_easyocr_reader(self):
        """Deep learning PyTorch EasyOCR fallback."""
        if self._easyocr_reader is None:
            import easyocr
            self._easyocr_reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
        return self._easyocr_reader

    def extract_text_rapidocr(self, image_path: str) -> Dict[str, Any]:
        engine = self._get_rapidocr_engine()
        result, elapse = engine(image_path)
        
        if not result:
            return {
                "engine": "RapidOCR (PP-OCRv4 CPU)",
                "full_text": "",
                "lines": [],
                "image_path": image_path
            }

        # Sort items vertically (top-to-bottom), then horizontally
        # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        sorted_results = sorted(result, key=lambda x: (x[0][0][1], x[0][0][0]))
        
        lines = []
        full_text_parts = []
        
        for bbox, text, prob in sorted_results:
            text = str(text).strip()
            if not text:
                continue
            full_text_parts.append(text)
            lines.append({
                "text": text,
                "confidence": float(prob) if prob else 0.9,
                "bbox": bbox
            })
            
        full_text = "\n".join(full_text_parts)
        
        return {
            "engine": "RapidOCR (PP-OCRv4 CPU)",
            "full_text": full_text,
            "lines": lines,
            "image_path": image_path
        }

    def extract_text_easyocr(self, image_path: str) -> Dict[str, Any]:
        reader = self._get_easyocr_reader()
        results = reader.readtext(image_path)
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

    def extract(self, image_path: str, prefer: str = "rapidocr") -> Dict[str, Any]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        pref = prefer.lower()
        if pref in ("rapidocr", "ppocr", "paddleocr", "default"):
            try:
                return self.extract_text_rapidocr(image_path)
            except Exception:
                return self.extract_text_easyocr(image_path)
        elif pref == "easyocr":
            try:
                return self.extract_text_easyocr(image_path)
            except Exception:
                return self.extract_text_rapidocr(image_path)
        elif pref == "tesseract":
            try:
                return self.extract_text_tesseract(image_path)
            except Exception:
                return self.extract_text_rapidocr(image_path)
        else:
            return self.extract_text_rapidocr(image_path)

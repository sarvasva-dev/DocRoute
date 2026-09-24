"""Tesseract OCR Integration Wrapper for DocRoute."""
import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
import pytesseract
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# System and Local Tesseract Binary Paths
STANDARD_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\ProgramData\chocolatey\bin\tesseract.exe",
]

# Local Project Tessdata Path
LOCAL_TESSDATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tessdata"))

class TesseractOCREngine:
    """Wrapper class for executing Tesseract OCR with localized tessdata and binary resolution."""

    def __init__(self, tesseract_cmd: Optional[str] = None, tessdata_dir: Optional[str] = None):
        """Initializes Tesseract engine and verifies binary & language configuration."""
        self.tesseract_cmd = tesseract_cmd or self._find_tesseract_binary()
        if self.tesseract_cmd and os.path.exists(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        self.tessdata_dir = tessdata_dir or (LOCAL_TESSDATA_DIR if os.path.exists(LOCAL_TESSDATA_DIR) else None)
        self.is_available = self._check_availability()

    def _find_tesseract_binary(self) -> Optional[str]:
        """Locates tesseract executable on Windows system or environment PATH."""
        for path in STANDARD_TESSERACT_PATHS:
            if os.path.exists(path):
                return path
        try:
            # Check if tesseract is in PATH
            ver = pytesseract.get_tesseract_version()
            return "tesseract"
        except Exception:
            return None

    def _check_availability(self) -> bool:
        """Verifies if Tesseract OCR binary executes cleanly."""
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR binary verified: {pytesseract.pytesseract.tesseract_cmd}")
            return True
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
            return False

    def get_supported_languages(self) -> List[str]:
        """Returns list of installed Tesseract language codes."""
        if not self.is_available:
            return []
        try:
            if self.tessdata_dir and os.path.exists(self.tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = self.tessdata_dir
                config = f'--tessdata-dir {self.tessdata_dir}'
            else:
                config = ""
            langs = pytesseract.get_languages(config=config)
            return langs
        except Exception as e:
            logger.warning(f"Failed to query Tesseract languages: {e}")
            return ["eng"]

    def extract_text(
        self, image: Any, lang: str = "eng", psm: int = 6
    ) -> Tuple[str, float, List[Dict[str, Any]]]:
        """Performs OCR on an image buffer or PIL Image.
        
        Args:
            image: PIL Image or OpenCV NumPy array
            lang: Language code (e.g. eng, hin, eng+hin)
            psm: Page segmentation mode (default 6: uniform block of text)
            
        Returns:
            Tuple of (extracted_text, average_confidence, word_boxes)
        """
        if not self.is_available:
            return "", 0.0, []

        try:
            if isinstance(image, np.ndarray):
                pil_img = Image.fromarray(image)
            else:
                pil_img = image

            config_parts = [f"--psm {psm}"]
            if self.tessdata_dir and os.path.exists(self.tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = self.tessdata_dir
                config_parts.append(f'--tessdata-dir {self.tessdata_dir}')
            config_str = " ".join(config_parts)

            # Check if requested language is available, fallback to eng if missing
            avail_langs = self.get_supported_languages()
            target_langs = [l for l in lang.split("+") if l in avail_langs]
            final_lang = "+".join(target_langs) if target_langs else "eng"

            # Execute OCR text extraction
            text = pytesseract.image_to_string(pil_img, lang=final_lang, config=config_str)

            # Execute OCR detailed word telemetry
            data = pytesseract.image_to_data(
                pil_img, lang=final_lang, config=config_str, output_type=pytesseract.Output.DICT
            )

            word_boxes = []
            confidences = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                w_text = data["text"][i].strip()
                conf = float(data["conf"][i])
                if w_text and conf >= 0:
                    confidences.append(conf)
                    word_boxes.append({
                        "text": w_text,
                        "confidence": conf,
                        "bbox": [
                            float(data["left"][i]),
                            float(data["top"][i]),
                            float(data["left"][i] + data["width"][i]),
                            float(data["top"][i] + data["height"][i])
                        ]
                    })

            avg_conf = float(np.mean(confidences)) if confidences else 0.0
            return text.strip(), avg_conf, word_boxes

        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            return "", 0.0, []

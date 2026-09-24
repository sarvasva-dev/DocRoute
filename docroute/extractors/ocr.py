"""OCR Extractor wrapping OpenCV Preprocessing and Tesseract OCR Engine."""
import logging
import uuid
import io
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import cv2
from PIL import Image
import numpy as np

from docroute.extractors.base import BaseExtractor
from docroute.models.extraction import PageExtraction
from docroute.models.profile import PageProfile
from docroute.models.quality import QualityScore
from docroute.models.provenance import ProvenanceRecord
from docroute.ocr.preprocessing import ImagePreprocessor
from docroute.ocr.tesseract import TesseractOCREngine

logger = logging.getLogger(__name__)

class OCRExtractor(BaseExtractor):
    """Executes image rendering, OpenCV preprocessing, and Tesseract OCR for scanned pages."""

    def __init__(self, ocr_engine: Optional[TesseractOCREngine] = None, dpi: int = 200):
        """Initializes OCR Extractor.
        
        Args:
            ocr_engine: Configured TesseractOCREngine instance
            dpi: Resolution for page rasterization (default 200 DPI for high quality & low RAM)
        """
        self.ocr_engine = ocr_engine or TesseractOCREngine()
        self.dpi = dpi

    def render_page_to_cv2(self, file_path: str, page_number: int) -> np.ndarray:
        """Renders PDF page or loads image file into OpenCV BGR numpy array."""
        page_idx = page_number - 1
        if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
            pil_img = Image.open(file_path)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        with fitz.open(file_path) as doc:
            if page_idx < 0 or page_idx >= len(doc):
                raise ValueError(f"Page number {page_number} out of bounds")
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=self.dpi)
            img_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_bytes))
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def extract_page(
        self, file_path: str, page_number: int, profile: PageProfile
    ) -> PageExtraction:
        """Executes full OCR pipeline: rendering -> preprocessing -> OCR -> provenance."""
        doc_id = file_path
        provenance_records: List[ProvenanceRecord] = []

        try:
            # 1. Render page image
            raw_cv2_img = self.render_page_to_cv2(file_path, page_number)

            # 2. OpenCV Preprocessing
            prep_img, prep_meta = ImagePreprocessor.preprocess_for_ocr(
                raw_cv2_img, apply_deskew=True, apply_denoise=False
            )

            # 3. Language selection (English + Hindi if hint present)
            lang = "eng"
            if "hin" in profile.language_hints:
                lang = "eng+hin"

            # 4. Execute Tesseract OCR
            ocr_text, avg_conf, word_boxes = self.ocr_engine.extract_text(
                prep_img, lang=lang, psm=6
            )

            # 5. Build Provenance Records for OCR words/blocks
            for w in word_boxes:
                rec = ProvenanceRecord(
                    record_id=f"prov-{uuid.uuid4().hex[:8]}",
                    document_id=doc_id,
                    page_number=page_number,
                    extraction_method="ocr",
                    engine="opencv+tesseract",
                    bbox=w["bbox"],
                    text_snippet=w["text"],
                    confidence=w["confidence"] / 100.0,
                    source_element="ocr_word",
                    routing_reasoning=(
                        f"OCR invoked due to low native text quality score. "
                        f"Deskew angle: {prep_meta.get('deskew_angle', 0.0):.2f}°."
                    )
                )
                provenance_records.append(rec)

            # 6. Quality Score
            quality = QualityScore(
                native_text_density=profile.text_density,
                garbage_ratio=0.0,
                printable_char_ratio=1.0,
                dictionary_word_ratio=1.0 if ocr_text else 0.0,
                ocr_confidence=avg_conf,
                overall_score=min(1.0, avg_conf / 100.0) if avg_conf > 0 else 0.0,
                threshold_applied=0.5,
                extraction_route="ocr",
                fallback_triggered=True,
                reasoning=f"OCR executed cleanly with average confidence {avg_conf:.1f}%."
            )

            return PageExtraction(
                page_number=page_number,
                text=ocr_text,
                extraction_method="ocr",
                quality=quality,
                tables=[],
                provenance=provenance_records
            )

        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path} page {page_number}: {e}")
            quality = QualityScore(
                native_text_density=0.0,
                garbage_ratio=1.0,
                printable_char_ratio=0.0,
                overall_score=0.0,
                extraction_route="ocr_error",
                fallback_triggered=True,
                reasoning=f"OCR execution failure: {e}"
            )
            return PageExtraction(
                page_number=page_number,
                text="",
                extraction_method="ocr",
                quality=quality,
                tables=[],
                provenance=[]
            )

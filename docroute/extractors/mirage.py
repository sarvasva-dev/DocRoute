"""Mirage Vision Extractor for DocRoute (Fallback Vision Engine)."""
import os
import sys
import json
import uuid
import shutil
import tempfile
import logging
import subprocess
from typing import List, Dict, Any, Optional

import fitz
from PIL import Image

from docroute.extractors.base import BaseExtractor
from docroute.models.extraction import PageExtraction
from docroute.models.profile import PageProfile
from docroute.models.quality import QualityScore
from docroute.models.provenance import ProvenanceRecord
from docroute.models.table import TableData

logger = logging.getLogger(__name__)

DEFAULT_AKSHAR_BIN = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "Desktop", "minor project", "mirage ai", "target", "release", "akshar")
)

class MirageExtractor(BaseExtractor):
    """Executes Cactus Mirage vision model extraction via Akshar --mode vision."""

    def __init__(self, binary_path: Optional[str] = None, dpi: int = 150):
        self.binary_path = binary_path or os.environ.get("AKSHAR_BIN", DEFAULT_AKSHAR_BIN)
        self.dpi = dpi
        if not os.path.exists(self.binary_path):
            found = shutil.which("akshar")
            if found:
                self.binary_path = found

    def extract_page(
        self, file_path: str, page_number: int, profile: PageProfile
    ) -> PageExtraction:
        """Executes Mirage vision model on the target page."""
        doc_id = os.path.basename(file_path)
        temp_img_path = None

        try:
            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
                target_image_path = file_path
            else:
                with fitz.open(file_path) as doc:
                    page_idx = page_number - 1
                    if page_idx < 0 or page_idx >= len(doc):
                        raise ValueError(f"Page number {page_number} out of bounds")
                    page = doc[page_idx]
                    pix = page.get_pixmap(dpi=self.dpi)
                    fd, temp_img_path = tempfile.mkstemp(suffix=f"_mirage_p{page_number}.png")
                    os.close(fd)
                    pix.save(temp_img_path)
                    target_image_path = temp_img_path

            # Invoke Akshar with --mode vision (calls Cactus Mirage describe)
            cmd = [self.binary_path, target_image_path, "--mode", "vision", "--json"]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Mirage vision CLI failed: {proc.stderr}")

            out_data = json.loads(proc.stdout)
            ocr_text = out_data.get("text", "")
            meta = out_data.get("meta", {})

            provenance_records = []
            for l in out_data.get("lines", []):
                rec = ProvenanceRecord(
                    record_id=f"prov-{uuid.uuid4().hex[:8]}",
                    document_id=doc_id,
                    page_number=page_number,
                    extraction_method="vision",
                    engine="cactus_mirage",
                    bbox=l.get("bbox", [0, 0, 0, 0]),
                    text_snippet=l.get("text", ""),
                    confidence=float(l.get("confidence", 0.75)),
                    source_element="vision_object",
                    routing_reasoning="Extracted via Cactus Mirage vision describe."
                )
                provenance_records.append(rec)

            quality = QualityScore(
                native_text_density=profile.text_density,
                garbage_ratio=0.0,
                printable_char_ratio=1.0,
                dictionary_word_ratio=1.0 if ocr_text else 0.0,
                ocr_confidence=75.0,
                overall_score=0.75,
                threshold_applied=0.5,
                extraction_route="mirage_vision",
                fallback_triggered=True,
                reasoning=f"Mirage vision describe completed in {meta.get('elapsed_ms', 0):.1f}ms."
            )

            return PageExtraction(
                page_number=page_number,
                width=profile.width,
                height=profile.height,
                text=ocr_text,
                extraction_method="vision",
                quality=quality,
                tables=[],
                provenance=provenance_records
            )

        except Exception as e:
            logger.error(f"Mirage extraction failed for {file_path} page {page_number}: {e}")
            quality = QualityScore(
                native_text_density=0.0,
                garbage_ratio=1.0,
                printable_char_ratio=0.0,
                overall_score=0.0,
                extraction_route="mirage_error",
                fallback_triggered=True,
                reasoning=f"Mirage execution failure: {e}"
            )
            return PageExtraction(
                page_number=page_number,
                text="",
                extraction_method="vision",
                quality=quality,
                tables=[],
                provenance=[]
            )
        finally:
            if temp_img_path and os.path.exists(temp_img_path):
                try:
                    os.remove(temp_img_path)
                except OSError:
                    pass

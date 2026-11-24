"""Akshar OCR & Document Intelligence Extractor for DocRoute."""
import os
import sys
import json
import uuid
import shutil
import tempfile
import logging
import subprocess
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
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

class AksharExtractor(BaseExtractor):
    """Executes high-performance OCR, table extraction, and provenance via Akshar engine."""

    def __init__(self, binary_path: Optional[str] = None, dpi: int = 150):
        """Initializes Akshar Extractor.
        
        Args:
            binary_path: Path to the compiled `akshar` release binary.
            dpi: Resolution for page rasterization if input is PDF (default 150 DPI).
        """
        self.binary_path = binary_path or os.environ.get("AKSHAR_BIN", DEFAULT_AKSHAR_BIN)
        self.dpi = dpi
        if not os.path.exists(self.binary_path):
            # Check system PATH
            found = shutil.which("akshar")
            if found:
                self.binary_path = found

    def extract_page(
        self, file_path: str, page_number: int, profile: PageProfile
    ) -> PageExtraction:
        """Executes Akshar extraction pipeline on a specific document page."""
        doc_id = os.path.basename(file_path)
        temp_img_path = None

        try:
            # 1. Prepare image for target page
            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
                target_image_path = file_path
            else:
                # Rasterize PDF page
                with fitz.open(file_path) as doc:
                    page_idx = page_number - 1
                    if page_idx < 0 or page_idx >= len(doc):
                        raise ValueError(f"Page number {page_number} out of bounds")
                    page = doc[page_idx]
                    pix = page.get_pixmap(dpi=self.dpi)
                    fd, temp_img_path = tempfile.mkstemp(suffix=f"_p{page_number}.png")
                    os.close(fd)
                    pix.save(temp_img_path)
                    target_image_path = temp_img_path

            # 2. Invoke Akshar CLI
            cmd = [self.binary_path, target_image_path, "--json"]
            env = os.environ.copy()
            # Set TESSDATA_PREFIX if available in Akshar assets
            tess_dir = os.path.abspath(os.path.join(os.path.dirname(self.binary_path), "..", "..", "assets", "tessdata"))
            if os.path.exists(tess_dir):
                env["TESSDATA_PREFIX"] = tess_dir

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            if proc.returncode != 0:
                raise RuntimeError(f"Akshar CLI exited with code {proc.returncode}: {proc.stderr}")

            out_data = json.loads(proc.stdout)
            ocr_text = out_data.get("text", "")
            meta = out_data.get("meta", {})
            engine_name = meta.get("engine", "akshar")

            # 3. Provenance records
            provenance_records: List[ProvenanceRecord] = []
            lines = out_data.get("lines", [])
            total_conf = 0.0
            conf_count = 0

            for l in lines:
                conf = float(l.get("confidence", 0.85))
                total_conf += conf
                conf_count += 1
                rec = ProvenanceRecord(
                    record_id=f"prov-{uuid.uuid4().hex[:8]}",
                    document_id=doc_id,
                    page_number=page_number,
                    extraction_method="ocr",
                    engine=f"akshar/{engine_name}",
                    bbox=l.get("bbox", [0, 0, 0, 0]),
                    text_snippet=l.get("text", ""),
                    confidence=min(1.0, conf if conf <= 1.0 else conf / 100.0),
                    source_element="ocr_line",
                    routing_reasoning=f"Extracted by Akshar {engine_name} with route {meta.get('auto_route', 'auto')}."
                )
                provenance_records.append(rec)

            avg_conf = (total_conf / conf_count) if conf_count > 0 else 0.85
            if avg_conf > 1.0:
                avg_conf = avg_conf / 100.0

            # 4. Tables
            tables: List[TableData] = []
            for t_raw in out_data.get("tables", []):
                headers = t_raw.get("headers", [])
                rows = t_raw.get("rows", [])
                md = t_raw.get("markdown", "")
                tables.append(TableData(
                    table_id=f"tbl-{uuid.uuid4().hex[:8]}",
                    page_number=page_number,
                    headers=headers,
                    rows=rows,
                    markdown=md,
                    num_rows=len(rows) + (1 if headers else 0),
                    num_cols=len(headers) if headers else (len(rows[0]) if rows else 0),
                    extraction_method="akshar-table",
                    confidence=0.95
                ))

            # 5. Quality Score
            quality = QualityScore(
                native_text_density=profile.text_density,
                garbage_ratio=0.0,
                printable_char_ratio=1.0,
                dictionary_word_ratio=1.0 if ocr_text else 0.0,
                ocr_confidence=avg_conf * 100.0,
                overall_score=min(1.0, max(0.5, avg_conf)),
                threshold_applied=0.5,
                extraction_route="akshar_vision",
                fallback_triggered=True,
                reasoning=(
                    f"Akshar executed in {meta.get('elapsed_ms', 0):.1f}ms. "
                    f"Route: {meta.get('auto_route', 'standard_ocr')}. "
                    f"Lines: {len(lines)}, Tables: {len(tables)}."
                )
            )

            return PageExtraction(
                page_number=page_number,
                width=profile.width,
                height=profile.height,
                text=ocr_text,
                extraction_method="ocr",
                quality=quality,
                tables=tables,
                provenance=provenance_records
            )

        except Exception as e:
            logger.error(f"Akshar extraction failed for {file_path} page {page_number}: {e}")
            quality = QualityScore(
                native_text_density=0.0,
                garbage_ratio=1.0,
                printable_char_ratio=0.0,
                overall_score=0.0,
                extraction_route="akshar_error",
                fallback_triggered=True,
                reasoning=f"Akshar execution failure: {e}"
            )
            return PageExtraction(
                page_number=page_number,
                text="",
                extraction_method="ocr",
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

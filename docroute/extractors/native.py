"""PyMuPDF Native Text and Layout Extractor."""
import logging
import uuid
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF

from docroute.extractors.base import BaseExtractor
from docroute.models.extraction import PageExtraction
from docroute.models.profile import PageProfile
from docroute.models.quality import QualityScore
from docroute.models.provenance import ProvenanceRecord

logger = logging.getLogger(__name__)

class NativePDFExtractor(BaseExtractor):
    """Extracts native text, font blocks, and element coordinates using PyMuPDF."""

    def extract_page(
        self, file_path: str, page_number: int, profile: PageProfile, fitz_doc: Optional[fitz.Document] = None
    ) -> PageExtraction:
        """Extracts native text layer and block-level provenance from PDF page."""
        doc_id = file_path
        page_idx = page_number - 1
        extracted_text_blocks: List[str] = []
        provenance_records: List[ProvenanceRecord] = []

        try:
            doc_context = fitz_doc if fitz_doc is not None else fitz.open(file_path)
            try:
                if page_idx < 0 or page_idx >= len(doc_context):
                    raise ValueError(f"Page number {page_number} out of bounds (1-{len(doc_context)})")
                
                page = doc_context[page_idx]
                blocks = page.get_text("blocks")  # returns list of (x0, y0, x1, y1, text, block_no, block_type)

                for b in blocks:
                    bbox = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
                    b_text = b[4].strip() if len(b) > 4 else ""
                    b_type = b[5] if len(b) > 5 else 0

                    if b_text and b_type == 0:  # 0 indicates text block
                        extracted_text_blocks.append(b_text)
                        rec = ProvenanceRecord(
                            record_id=f"prov-{uuid.uuid4().hex[:8]}",
                            document_id=doc_id,
                            page_number=page_number,
                            extraction_method="native",
                            engine="pymupdf-native",
                            bbox=bbox,
                            text_snippet=b_text[:100],
                            confidence=1.0,
                            source_element="text_block",
                            routing_reasoning="High native text density detected by Document Profiler."
                        )
                        provenance_records.append(rec)
            finally:
                if fitz_doc is None and doc_context:
                    doc_context.close()

            full_text = "\n\n".join(extracted_text_blocks)
            
            # Simple quality score calculation for clean native text
            quality = QualityScore(
                native_text_density=profile.text_density,
                garbage_ratio=0.0,
                printable_char_ratio=1.0,
                dictionary_word_ratio=1.0,
                overall_score=1.0,
                threshold_applied=0.5,
                extraction_route="native",
                fallback_triggered=False,
                reasoning="Native vector text extracted successfully with PyMuPDF."
            )

            return PageExtraction(
                page_number=page_number,
                width=profile.width,
                height=profile.height,
                text=full_text,
                extraction_method="native",
                quality=quality,
                tables=[],
                provenance=provenance_records
            )

        except Exception as e:
            logger.error(f"Native extraction failed for {file_path} page {page_number}: {e}")
            quality = QualityScore(
                native_text_density=0.0,
                garbage_ratio=1.0,
                printable_char_ratio=0.0,
                overall_score=0.0,
                extraction_route="native_error",
                fallback_triggered=False,
                reasoning=f"Native extraction error: {e}"
            )
            return PageExtraction(
                page_number=page_number,
                text="",
                extraction_method="native",
                quality=quality,
                tables=[],
                provenance=[]
            )

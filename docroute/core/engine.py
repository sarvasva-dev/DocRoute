"""DocRoute Main Orchestrator Engine."""
import os
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
import fitz
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from docroute.models.document import StructuredDocument
from docroute.models.profile import DocumentProfile, PageProfile
from docroute.models.extraction import PageExtraction
from docroute.models.quality import QualityScore
from docroute.models.api import ProcessingOptions
from docroute.core.profiler import DocumentProfiler
from docroute.extractors.native import NativePDFExtractor
from docroute.extractors.ocr import OCRExtractor
from docroute.extractors.tables import TableExtractor
from docroute.routing.quality import QualityAssessor
from docroute.routing.router import OCRRouter
from docroute.provenance.tracker import ProvenanceTracker

logger = logging.getLogger(__name__)

ENGINE_VERSION = "1.0.0"

class DocRouteEngine:
    """Adaptive Document Intelligence Engine main orchestrator."""

    def __init__(self, options: Optional[ProcessingOptions] = None):
        """Initializes DocRoute engine with processing options."""
        self.options = options or ProcessingOptions()
        self.profiler = DocumentProfiler()
        self.native_extractor = NativePDFExtractor()
        self.ocr_extractor = OCRExtractor()
        self.table_extractor = TableExtractor()
        self.router = OCRRouter(default_threshold=self.options.ocr_threshold)

    def process_document(
        self, file_path: str, options_override: Optional[ProcessingOptions] = None
    ) -> StructuredDocument:
        """Executes full DocRoute document processing pipeline.
        
        Pipeline:
        1. Profile Document (geometry, native text, image count, scan likelihood)
        2. Iterate Pages:
           a. Extract Native text
           b. Assess Native Quality
           c. Route: Accept Native OR Invoke OCR Fallback
           d. Extract Tables if enabled
           e. Build Page-level Provenance
        3. Assemble Overall Quality & StructuredDocument
        """
        opts = options_override or self.options
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc_id = os.path.basename(file_path)
        logger.info(f"Initiating DocRoute processing for: {doc_id}")

        # Step 1: Profile Document
        doc_profile = self.profiler.profile_document(file_path, max_pages=opts.max_pages)
        provenance_tracker = ProvenanceTracker(document_id=doc_id)
        page_extractions: List[PageExtraction] = []
        overall_page_scores: List[float] = []
        fallback_counts = 0

        # Step 2: Page-by-Page Processing
        pages_to_process = doc_profile.pages[:opts.max_pages] if opts.max_pages else doc_profile.pages
        doc_fitz = fitz.open(file_path) if file_path.lower().endswith(".pdf") else None
        try:
            for p_prof in pages_to_process:
                p_num = p_prof.page_number
                page_area = max(1.0, p_prof.width * p_prof.height)

                # Force OCR check
                if opts.force_ocr:
                    logger.info(f"Page {p_num}: Force OCR enabled.")
                    page_ext = self.ocr_extractor.extract_page(file_path, p_num, p_prof)
                    page_ext.quality.fallback_triggered = True
                    page_ext.quality.reasoning = "Force OCR enabled by caller."
                    fallback_counts += 1
                else:
                    # Native Extraction
                    native_ext = self.native_extractor.extract_page(file_path, p_num, p_prof, fitz_doc=doc_fitz)
                    native_quality = QualityAssessor.assess_native_quality(
                        native_ext.text, p_prof.native_char_count, page_area, threshold=opts.ocr_threshold
                    )

                    # Router decision
                    should_ocr, route_reasoning = self.router.decide_route(
                        p_prof, native_quality, threshold=opts.ocr_threshold
                    )

                    if should_ocr:
                        logger.info(f"Page {p_num}: Invoking OCR fallback. ({route_reasoning})")
                        page_ext = self.ocr_extractor.extract_page(file_path, p_num, p_prof)
                        page_ext.quality.fallback_triggered = True
                        page_ext.quality.reasoning = route_reasoning
                        fallback_counts += 1
                    else:
                        logger.info(f"Page {p_num}: Accepting Native extraction. ({route_reasoning})")
                        page_ext = native_ext
                        page_ext.quality = native_quality
                        page_ext.quality.reasoning = route_reasoning

                # Extract Tables if enabled and page has table layout signals
                if opts.extract_tables and p_prof.table_likelihood > 0.05:
                    extracted_tables = self.table_extractor.extract_tables_from_page(file_path, p_num, fitz_doc=doc_fitz)
                    page_ext.tables = extracted_tables

                # Track Provenance
                provenance_tracker.add_records(page_ext.provenance)
                page_extractions.append(page_ext)
                overall_page_scores.append(page_ext.quality.overall_score)
        finally:
            if doc_fitz:
                doc_fitz.close()

        # Step 3: Compute Document Overall Quality Summary
        avg_score = float(np.mean(overall_page_scores)) if overall_page_scores else 0.0
        doc_quality = QualityScore(
            native_text_density=doc_profile.avg_text_density,
            garbage_ratio=0.0,
            printable_char_ratio=1.0,
            dictionary_word_ratio=1.0,
            overall_score=avg_score,
            threshold_applied=opts.ocr_threshold,
            extraction_route="hybrid" if fallback_counts > 0 else "native",
            fallback_triggered=fallback_counts > 0,
            reasoning=(
                f"Processed {doc_profile.page_count} pages. "
                f"OCR fallback triggered on {fallback_counts}/{doc_profile.page_count} pages. "
                f"Average quality score: {avg_score:.2f}."
            )
        )

        metadata_catalog = {
            "filename": doc_id,
            "filepath": file_path,
            "page_count": doc_profile.page_count,
            "is_scanned": doc_profile.is_scanned_pdf,
            "is_native": doc_profile.is_native_pdf,
            "primary_language": doc_profile.primary_language,
            "pdf_metadata": doc_profile.pdf_metadata,
            "options_used": opts.model_dump()
        }

        return StructuredDocument(
            document_id=doc_id,
            pages=page_extractions,
            metadata=metadata_catalog,
            overall_quality=doc_quality,
            engine_version=ENGINE_VERSION
        )

    def generate_visual_debug_page(
        self, file_path: str, page_number: int, output_image_path: str
    ) -> Dict[str, Any]:
        """Generates visual debug image for a page showing bounding boxes and route decisions."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Profile and process target page
        profile = self.profiler.profile_document(file_path)
        if page_number < 1 or page_number > profile.page_count:
            raise ValueError(f"Invalid page number {page_number}")

        p_prof = profile.pages[page_number - 1]
        p_ext = self.ocr_extractor.extract_page(file_path, page_number, p_prof)

        # Render original page to PIL Image
        raw_cv2 = self.ocr_extractor.render_page_to_cv2(file_path, page_number)
        pil_img = Image.fromarray(np.uint8(raw_cv2)).convert("RGB")
        draw = ImageDraw.Draw(pil_img)

        # Draw provenance bounding boxes
        for rec in p_ext.provenance:
            if rec.bbox and len(rec.bbox) == 4:
                x0, y0, x1, y1 = rec.bbox
                color = "red" if rec.extraction_method == "ocr" else "green"
                draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

        # Header banner
        draw.rectangle([0, 0, pil_img.width, 40], fill=(30, 30, 30))
        header_text = (
            f"DocRoute Debug Mode | Page {page_number} | Route: {p_ext.extraction_method.upper()} | "
            f"Quality: {p_ext.quality.overall_score:.2f} | Fallback: {p_ext.quality.fallback_triggered}"
        )
        draw.text((10, 10), header_text, fill=(255, 255, 255))

        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        pil_img.save(output_image_path)

        return {
            "page_number": page_number,
            "output_path": output_image_path,
            "extraction_method": p_ext.extraction_method,
            "quality_score": p_ext.quality.overall_score,
            "bounding_boxes_count": len(p_ext.provenance)
        }

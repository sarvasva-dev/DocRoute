"""Document Profiler Engine."""
import os
import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image

from docroute.models.profile import DocumentProfile, PageProfile

logger = logging.getLogger(__name__)

class DocumentProfiler:
    """Inspects PDFs and images to generate detailed document profiles and routing signals."""

    @classmethod
    def profile_document(cls, file_path: str, max_pages: Optional[int] = None) -> DocumentProfile:
        """Profiles document geometry, text density, image coverage, and scan likelihood.
        
        Args:
            file_path: Path to PDF or image file
            max_pages: Optional maximum pages to profile
            
        Returns:
            DocumentProfile containing page profiles and document-level metrics
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        doc_id = os.path.basename(file_path)
        is_pdf = file_path.lower().endswith(".pdf")

        if not is_pdf:
            return cls._profile_image_file(file_path, doc_id)

        page_profiles: List[PageProfile] = []
        pdf_meta: Dict[str, Any] = {}
        total_chars = 0
        scanned_page_count = 0
        native_page_count = 0
        table_heavy_page_count = 0
        image_heavy_page_count = 0
        lang_hints_set = set()

        try:
            with fitz.open(file_path) as doc:
                total_doc_pages = len(doc)
                pages_to_profile = min(total_doc_pages, max_pages) if max_pages else total_doc_pages
                pdf_meta = {
                    "format": doc.name,
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "producer": doc.metadata.get("producer", ""),
                    "creator": doc.metadata.get("creator", ""),
                    "creation_date": doc.metadata.get("creationDate", ""),
                    "encrypted": doc.is_encrypted,
                    "page_count": total_doc_pages
                }

                for page_idx in range(pages_to_profile):
                    page = doc[page_idx]
                    rect = page.rect
                    w, h = rect.width, rect.height
                    page_area = max(1.0, w * h)

                    # Extract native text for density calculation
                    n_text = page.get_text("text") or ""
                    n_char_count = len(n_text.strip())
                    total_chars += n_char_count

                    density = (float(n_char_count) / (page_area / 1000.0))

                    # Inspect embedded images
                    image_list = page.get_images(full=True)
                    image_count = len(image_list)

                    # Calculate image coverage area
                    total_img_area = 0.0
                    for img_info in image_list:
                        # Attempt to get image rect if available
                        total_img_area += page_area * 0.3  # heuristic coverage per embedded image

                    image_area_ratio = min(1.0, total_img_area / page_area) if image_count > 0 else 0.0

                    # Scan Likelihood score calculation
                    if n_char_count > 40 and image_count == 0:
                        scan_likelihood = 0.05
                    elif n_char_count < 20 and image_count > 0:
                        scan_likelihood = 0.95
                    elif n_char_count < 50:
                        scan_likelihood = 0.70
                    elif density < 0.2:
                        scan_likelihood = 0.40
                    else:
                        scan_likelihood = 0.05

                    if scan_likelihood > 0.6:
                        scanned_page_count += 1
                    else:
                        native_page_count += 1

                    # Table Likelihood calculation
                    # Check for horizontal/vertical lines before invoking heavy table finder
                    drawings = page.get_drawings()
                    has_table_lines = any(len(d.get("items", [])) >= 2 for d in drawings[:30]) if drawings else False
                    table_count = 0
                    if has_table_lines:
                        tabs = page.find_tables()
                        tables_list = tabs.tables if hasattr(tabs, "tables") else []
                        table_count = len(tables_list)
                    
                    table_likelihood = min(1.0, table_count * 0.5) if table_count > 0 else 0.05

                    if table_count > 0:
                        table_heavy_page_count += 1

                    if image_count > 2 or image_area_ratio > 0.5:
                        image_heavy_page_count += 1

                    # Language hints: inspect Devanagari script range for Hindi
                    devanagari_chars = sum(1 for c in n_text if '\u0900' <= c <= '\u097F')
                    page_lang_hints = ["eng"]
                    if devanagari_chars > 10:
                        page_lang_hints.append("hin")
                        lang_hints_set.add("hin")
                    else:
                        lang_hints_set.add("eng")

                    p_profile = PageProfile(
                        page_number=page_idx + 1,
                        width=w,
                        height=h,
                        native_char_count=n_char_count,
                        text_density=density,
                        image_count=image_count,
                        image_area_ratio=image_area_ratio,
                        scan_likelihood=scan_likelihood,
                        table_likelihood=table_likelihood,
                        language_hints=page_lang_hints,
                        quality_signals={
                            "has_native_text": n_char_count > 50,
                            "table_count": table_count,
                            "devanagari_char_count": devanagari_chars
                        }
                    )
                    page_profiles.append(p_profile)

            page_cnt = max(1, len(page_profiles))
            avg_density = total_chars / page_cnt

            is_scanned = scanned_page_count == page_cnt
            is_native = native_page_count == page_cnt
            is_mixed = not is_scanned and not is_native

            primary_lang = "hin" if "hin" in lang_hints_set and len(lang_hints_set) == 1 else "eng"
            if "hin" in lang_hints_set and "eng" in lang_hints_set:
                primary_lang = "eng+hin"

            return DocumentProfile(
                document_id=doc_id,
                page_count=page_cnt,
                avg_text_density=avg_density,
                is_scanned_pdf=is_scanned,
                is_native_pdf=is_native,
                is_mixed_pdf=is_mixed,
                is_image_heavy=image_heavy_page_count > 0,
                is_table_heavy=table_heavy_page_count > 0,
                primary_language=primary_lang,
                pdf_metadata=pdf_meta,
                pages=page_profiles
            )

        except Exception as e:
            logger.error(f"Failed to profile document {file_path}: {e}")
            raise RuntimeError(f"Document profiling failed: {e}") from e

    @classmethod
    def _profile_image_file(cls, file_path: str, doc_id: str) -> DocumentProfile:
        """Profiles a standalone raster image file as a 1-page scanned document."""
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                page_area = max(1.0, float(w * h))
                
                p_profile = PageProfile(
                    page_number=1,
                    width=float(w),
                    height=float(h),
                    native_char_count=0,
                    text_density=0.0,
                    image_count=1,
                    image_area_ratio=1.0,
                    scan_likelihood=1.0,
                    table_likelihood=0.2,
                    language_hints=["eng"],
                    quality_signals={"is_raw_image": True}
                )

                return DocumentProfile(
                    document_id=doc_id,
                    page_count=1,
                    avg_text_density=0.0,
                    is_scanned_pdf=True,
                    is_native_pdf=False,
                    is_mixed_pdf=False,
                    is_image_heavy=True,
                    is_table_heavy=False,
                    primary_language="eng",
                    pdf_metadata={"format": img.format, "mode": img.mode},
                    pages=[p_profile]
                )
        except Exception as e:
            raise RuntimeError(f"Image profiling failed for {file_path}: {e}") from e

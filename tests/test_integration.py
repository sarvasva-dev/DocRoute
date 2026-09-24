"""End-to-End Un-Mocked Integration Test."""
import os
import pytest
from docroute.core.engine import DocRouteEngine
from docroute.models.api import ProcessingOptions

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data"))

def test_full_pipeline_mixed_document():
    """Unmocked integration test on a 2-page mixed document (Native page 1 + Scanned page 2)."""
    pdf_path = os.path.join(BENCHMARK_DIR, "mixed_document.pdf")
    opts = ProcessingOptions(ocr_threshold=0.5, extract_tables=True)
    engine = DocRouteEngine(options=opts)

    # Execute full pipeline
    structured_doc = engine.process_document(pdf_path)

    assert structured_doc.document_id == "mixed_document.pdf"
    assert len(structured_doc.pages) == 2
    assert structured_doc.overall_quality.fallback_triggered is True

    # Page 1 must accept Native route
    p1 = structured_doc.pages[0]
    assert p1.page_number == 1
    assert p1.extraction_method == "native"
    assert "Mixed PDF Document - Page 1" in p1.text
    assert len(p1.provenance) > 0

    # Page 2 must trigger OCR fallback route
    p2 = structured_doc.pages[1]
    assert p2.page_number == 2
    assert p2.extraction_method == "ocr"
    assert any(k in p2.text for k in ["Invoice", "Page", "INV", "Number"])
    assert len(p2.provenance) > 0
    assert p2.quality.fallback_triggered is True

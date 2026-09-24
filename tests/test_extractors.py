"""Unit tests for Native, OCR, and Table Extractors."""
import os
import pytest
from docroute.extractors.native import NativePDFExtractor
from docroute.extractors.ocr import OCRExtractor
from docroute.extractors.tables import TableExtractor
from docroute.core.profiler import DocumentProfiler

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data"))

def test_native_extractor():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    profile = DocumentProfiler.profile_document(pdf_path)
    extractor = NativePDFExtractor()
    page_ext = extractor.extract_page(pdf_path, 1, profile.pages[0])
    assert page_ext.page_number == 1
    assert "DocRoute Framework" in page_ext.text
    assert page_ext.extraction_method == "native"
    assert len(page_ext.provenance) > 0

def test_ocr_extractor():
    pdf_path = os.path.join(BENCHMARK_DIR, "scanned_page.pdf")
    profile = DocumentProfiler.profile_document(pdf_path)
    extractor = OCRExtractor()
    page_ext = extractor.extract_page(pdf_path, 1, profile.pages[0])
    assert page_ext.page_number == 1
    assert "CONFIDENTIAL" in page_ext.text or "FINANCIAL" in page_ext.text
    assert page_ext.extraction_method == "ocr"
    assert len(page_ext.provenance) > 0

def test_table_extractor():
    pdf_path = os.path.join(BENCHMARK_DIR, "table_heavy.pdf")
    extractor = TableExtractor()
    tables = extractor.extract_tables_from_page(pdf_path, 1)
    assert len(tables) >= 1
    tab = tables[0]
    assert tab.num_rows == 4
    assert tab.num_cols == 4
    assert "Quarter" in tab.headers or "Revenue" in tab.headers

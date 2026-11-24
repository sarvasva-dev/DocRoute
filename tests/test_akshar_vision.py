"""Tests for Akshar Vision Integration in DocRoute."""
import os
import pytest
from docroute import extract, DocRouteEngine, ProcessingOptions
from docroute.extractors.akshar import AksharExtractor, DEFAULT_AKSHAR_BIN
from docroute.models.profile import PageProfile

SMOKE_PDF = "/home/sarvasva/Desktop/minor project/mirage ai/tests/data/real_corpus/real_sample_smoke.pdf"

def test_akshar_binary_exists():
    assert os.path.exists(DEFAULT_AKSHAR_BIN), f"Akshar binary missing at {DEFAULT_AKSHAR_BIN}"

def test_akshar_extractor_direct():
    extractor = AksharExtractor(binary_path=DEFAULT_AKSHAR_BIN)
    profile = PageProfile(
        page_number=2,
        width=595.0,
        height=842.0,
        native_char_count=0,
        text_density=0.0,
        image_count=1,
        scan_likelihood=0.99
    )
    ext = extractor.extract_page(SMOKE_PDF, 2, profile)
    assert ext.extraction_method == "ocr"
    assert "12345" in ext.text
    assert ext.quality.overall_score >= 0.5
    assert len(ext.provenance) > 0
    assert "akshar" in ext.provenance[0].engine

def test_docroute_end_to_end_with_akshar_default():
    # Process 3-page hybrid smoke PDF with default vision="akshar"
    doc = extract(SMOKE_PDF, vision="akshar")
    assert len(doc.pages) == 3
    
    # Page 1: Native text (ms, never OCR'd)
    p1 = doc.pages[0]
    assert p1.extraction_method == "native"
    assert "Smoke Test" in p1.text
    assert p1.quality.fallback_triggered is False

    # Page 2: Scanned invoice (Akshar fallback invoked)
    p2 = doc.pages[1]
    assert p2.extraction_method == "ocr"
    assert "12345" in p2.text
    assert p2.quality.fallback_triggered is True

    # Page 3: Native text + 2D Table
    p3 = doc.pages[2]
    assert p3.extraction_method == "native"
    assert len(p3.tables) >= 1
    t0 = p3.tables[0]
    assert "Item" in t0.headers
    assert "Qty" in t0.headers
    assert "Price" in t0.headers

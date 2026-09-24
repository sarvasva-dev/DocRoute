"""Unit tests for Quality Assessment and Fallback Routing."""
import pytest
from docroute.routing.quality import QualityAssessor
from docroute.routing.router import OCRRouter
from docroute.models.profile import PageProfile
from docroute.models.quality import QualityScore

def test_quality_assessor_clean_text():
    text = "DocRoute Framework Executive Summary Core Performance Indicators."
    score = QualityAssessor.assess_native_quality(text, len(text), page_area_sq_pt=500000.0)
    assert score.overall_score > 0.5
    assert score.garbage_ratio == 0.0
    assert score.printable_char_ratio == 1.0

def test_quality_assessor_scanned_empty():
    text = ""
    score = QualityAssessor.assess_native_quality(text, 0, page_area_sq_pt=500000.0)
    assert score.overall_score == 0.0
    assert score.garbage_ratio == 1.0

def test_ocr_router_accept_native():
    router = OCRRouter(default_threshold=0.5)
    p_profile = PageProfile(
        page_number=1, width=595, height=842, native_char_count=300,
        text_density=1.5, image_count=0, image_area_ratio=0.0, scan_likelihood=0.05
    )
    native_quality = QualityScore(overall_score=0.8, garbage_ratio=0.0, native_text_density=1.5)
    should_ocr, reason = router.decide_route(p_profile, native_quality)
    assert should_ocr is False
    assert "Native Text Accepted" in reason

def test_ocr_router_trigger_fallback():
    router = OCRRouter(default_threshold=0.5)
    p_profile = PageProfile(
        page_number=1, width=595, height=842, native_char_count=5,
        text_density=0.01, image_count=1, image_area_ratio=0.8, scan_likelihood=0.95
    )
    native_quality = QualityScore(overall_score=0.1, garbage_ratio=0.8, native_text_density=0.01)
    should_ocr, reason = router.decide_route(p_profile, native_quality)
    assert should_ocr is True
    assert "OCR Fallback Triggered" in reason

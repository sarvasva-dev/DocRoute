"""Unit tests for Document Profiler."""
import os
import pytest
from docroute.core.profiler import DocumentProfiler

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data"))

def test_profile_native_pdf():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    profile = DocumentProfiler.profile_document(pdf_path)
    assert profile.page_count == 1
    assert profile.is_native_pdf is True
    assert profile.is_scanned_pdf is False
    assert profile.pages[0].native_char_count > 50
    assert profile.pages[0].scan_likelihood < 0.2

def test_profile_scanned_pdf():
    pdf_path = os.path.join(BENCHMARK_DIR, "scanned_page.pdf")
    profile = DocumentProfiler.profile_document(pdf_path)
    assert profile.page_count == 1
    assert profile.is_scanned_pdf is True
    assert profile.pages[0].scan_likelihood > 0.6

def test_profile_mixed_pdf():
    pdf_path = os.path.join(BENCHMARK_DIR, "mixed_document.pdf")
    profile = DocumentProfiler.profile_document(pdf_path)
    assert profile.page_count == 2
    assert profile.is_mixed_pdf is True
    assert profile.pages[0].scan_likelihood < 0.2
    assert profile.pages[1].scan_likelihood > 0.6

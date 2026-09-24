"""Integration tests for DocRoute CLI tool."""
import os
import sys
import subprocess
import json
import pytest
from tests.create_benchmark_dataset import build_benchmark_dataset

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "_generated"))
ENV = {"PYTHONPATH": ".", **os.environ}

@pytest.fixture(autouse=True, scope="module")
def ensure_test_dataset():
    if not os.path.exists(BENCHMARK_DIR) or not os.listdir(BENCHMARK_DIR):
        build_benchmark_dataset(BENCHMARK_DIR)

def extract_json_from_stdout(stdout: str) -> dict:
    """Extracts JSON dictionary substring starting from first '{'."""
    idx = stdout.find("{")
    if idx != -1:
        return json.loads(stdout[idx:])
    return json.loads(stdout)

def test_cli_inspect():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    res = subprocess.run([sys.executable, "-m", "docroute", "inspect", pdf_path], capture_output=True, text=True, env=ENV)
    assert res.returncode == 0
    assert "DocRoute Inspection" in res.stdout
    assert "Page Count" in res.stdout

def test_cli_profile():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    res = subprocess.run([sys.executable, "-m", "docroute", "profile", pdf_path], capture_output=True, text=True, env=ENV)
    assert res.returncode == 0
    data = extract_json_from_stdout(res.stdout)
    assert data["page_count"] == 1

def test_cli_extract_json():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    res = subprocess.run([sys.executable, "-m", "docroute", "extract", pdf_path, "--json"], capture_output=True, text=True, env=ENV)
    assert res.returncode == 0
    data = extract_json_from_stdout(res.stdout)
    assert "document_id" in data
    assert len(data["pages"]) == 1

def test_cli_ocr():
    pdf_path = os.path.join(BENCHMARK_DIR, "scanned_page.pdf")
    res = subprocess.run([sys.executable, "-m", "docroute", "ocr", pdf_path, "--json"], capture_output=True, text=True, env=ENV)
    assert res.returncode == 0
    data = extract_json_from_stdout(res.stdout)
    assert data["pages"][0]["extraction_method"] == "ocr"

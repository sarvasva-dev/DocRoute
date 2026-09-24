"""Integration tests for FastAPI REST API endpoints."""
import os
import pytest
from fastapi.testclient import TestClient
from docroute.api.app import app
from tests.create_benchmark_dataset import build_benchmark_dataset

client = TestClient(app)
BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "_generated"))

@pytest.fixture(autouse=True, scope="module")
def ensure_test_dataset():
    if not os.path.exists(BENCHMARK_DIR) or not os.listdir(BENCHMARK_DIR):
        build_benchmark_dataset(BENCHMARK_DIR)

def test_health_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "DocRoute Engine"

def test_document_upload_and_fetch():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    with open(pdf_path, "rb") as f:
        res = client.post(
            "/documents",
            files={"file": ("native_text.pdf", f, "application/pdf")},
            params={"ocr_threshold": 0.5}
        )
    assert res.status_code == 201
    doc_data = res.json()
    doc_id = doc_data["document_id"]
    assert doc_data["metadata"]["page_count"] == 1

    # Fetch document
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200

    # Fetch profile
    prof_res = client.get(f"/documents/{doc_id}/profile")
    assert prof_res.status_code == 200
    assert prof_res.json()["page_count"] == 1

    # Fetch pages
    pages_res = client.get(f"/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    assert len(pages_res.json()) == 1

    # Fetch plain text
    text_res = client.get(f"/documents/{doc_id}/text")
    assert text_res.status_code == 200
    assert "DocRoute Framework" in text_res.json()["text"]

    # Fetch quality
    q_res = client.get(f"/documents/{doc_id}/quality")
    assert q_res.status_code == 200
    assert q_res.json()["overall_score"] > 0.5

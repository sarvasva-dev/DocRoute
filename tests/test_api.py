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

def test_health_and_root_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "docroute-api"
    assert res.json()["status"] == "ok"

    ready_res = client.get("/ready")
    assert ready_res.status_code in [200, 503]

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["service"] == "docroute-api"

def test_v1_ocr_unified_endpoint():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    with open(pdf_path, "rb") as f:
        res = client.post(
            "/v1/ocr",
            files={"file": ("native_text.pdf", f, "application/pdf")},
            data={"language": "eng", "quality_threshold": "0.5"}
        )
    assert res.status_code == 200
    ocr_data = res.json()
    assert ocr_data["status"] == "completed"
    assert "text" in ocr_data
    assert "DocRoute Framework" in ocr_data["text"]
    assert "extraction" in ocr_data
    assert "quality" in ocr_data

def test_v1_document_upload_and_fetch():
    pdf_path = os.path.join(BENCHMARK_DIR, "native_text.pdf")
    with open(pdf_path, "rb") as f:
        res = client.post(
            "/v1/documents",
            files={"file": ("native_text.pdf", f, "application/pdf")},
            params={"ocr_threshold": 0.5}
        )
    assert res.status_code == 201
    doc_data = res.json()
    doc_id = doc_data["document_id"]
    assert doc_data["metadata"]["page_count"] == 1

    # Fetch document
    get_res = client.get(f"/v1/documents/{doc_id}")
    assert get_res.status_code == 200

    # Fetch profile
    prof_res = client.get(f"/v1/documents/{doc_id}/profile")
    assert prof_res.status_code == 200
    assert prof_res.json()["page_count"] == 1

    # Fetch pages
    pages_res = client.get(f"/v1/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    assert len(pages_res.json()) == 1

    # Fetch plain text
    text_res = client.get(f"/v1/documents/{doc_id}/text")
    assert text_res.status_code == 200
    assert "DocRoute Framework" in text_res.json()["text"]

    # Fetch Google Vision compatible schema
    vision_res = client.get(f"/v1/documents/{doc_id}/vision")
    assert vision_res.status_code == 200
    assert "responses" in vision_res.json()

    # Fetch Key-Value form pairs
    kv_res = client.get(f"/v1/documents/{doc_id}/kv-pairs")
    assert kv_res.status_code == 200
    assert isinstance(kv_res.json(), list)

    # Fetch quality
    q_res = client.get(f"/v1/documents/{doc_id}/quality")
    assert q_res.status_code == 200
    assert q_res.json()["overall_score"] > 0.5

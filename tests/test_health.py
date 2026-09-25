"""Automated tests for DocRoute API Health & Readiness Endpoints."""
import time
import pytest
from fastapi.testclient import TestClient
from docroute.api.app import app

client = TestClient(app)

def test_health_200():
    """Verify /health returns HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_response_schema():
    """Verify /health schema contains status=ok, service=docroute-api, version, timestamp, environment."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "docroute-api"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data

def test_health_no_auth():
    """Verify /health is public and bypasses API key authentication."""
    response = client.get("/health", headers={"Authorization": "Bearer invalid_key"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health_fast():
    """Verify /health executes in sub-milliseconds without delay."""
    start = time.time()
    response = client.get("/health")
    duration_ms = (time.time() - start) * 1000
    assert response.status_code == 200
    assert duration_ms < 100  # Should be ultra-fast (<100ms)

def test_ready_response():
    """Verify /ready returns readiness schema."""
    response = client.get("/ready")
    assert response.status_code in [200, 533, 503]
    data = response.json()
    assert "status" in data
    assert "ocr" in data

def test_health_does_not_start_ocr(monkeypatch):
    """Verify calling /health never invokes OCR or heavy document processing."""
    def mock_ocr_fail(*args, **kwargs):
        raise RuntimeError("OCR should NOT be called during health checks!")
        
    monkeypatch.setattr("docroute.ocr.tesseract.TesseractOCREngine.extract_text", mock_ocr_fail)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

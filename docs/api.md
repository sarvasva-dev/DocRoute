# DocRoute REST API Reference (v1)

DocRoute provides a versioned, production-grade REST API namespace under `/v1/` for document OCR, native PDF extraction, table matrix parsing, form key-value extraction, quality scoring, and spatial provenance tracking.

---

## Base URLs
- **Local Server**: `http://localhost:8000`
- **Render Production Server**: `https://YOUR-DOCROUTE-BACKEND.onrender.com`

---

## Authentication

Authentication is controlled via the `DOCROUTE_API_KEY` environment variable.

- **Local / Unrestricted Mode**: If `DOCROUTE_API_KEY` is not set on the server, all endpoints allow open access.
- **API Key Mode**: If set, pass your API key in requests using either header:
  - `Authorization: Bearer YOUR_API_KEY`
  - `X-API-Key: YOUR_API_KEY`

*Note: `/health`, `/ready`, `/`, `/docs`, and `/redoc` are public endpoints that always bypass authentication.*

---

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public lightweight health check. Returns `status: "ok"`. | No |
| `GET` | `/ready` | Readiness check verifying Tesseract binary availability. | No |
| `GET` | `/v1` | V1 API endpoint discovery catalog. | No |
| `POST` | `/v1/ocr` | Unified document extraction & OCR pipeline. | Optional |
| `POST` | `/v1/documents` | Upload & process document returning `StructuredDocument`. | Optional |
| `GET` | `/v1/documents/{id}` | Get structured document extraction JSON. | Optional |
| `GET` | `/v1/documents/{id}/pages` | Get page-by-page extractions list. | Optional |
| `GET` | `/v1/documents/{id}/text` | Get plain aggregated document text. | Optional |
| `GET` | `/v1/documents/{id}/tables` | Get extracted 2D table matrices list. | Optional |
| `GET` | `/v1/documents/{id}/quality` | Get document extraction quality score report. | Optional |
| `GET` | `/v1/documents/{id}/vision` | Get Google Cloud Vision compatible `AnnotateImageResponse` JSON. | Optional |
| `GET` | `/v1/documents/{id}/kv-pairs` | Get extracted Form Field Key-Value pairs list. | Optional |

---

## 1. Unified OCR & Document Extraction (`POST /v1/ocr`)

The primary developer endpoint for processing PDFs and image files (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.webp`).

### Request Parameters (Multipart Form Data)
- `file` *(file, required)*: Document file binary.
- `language` *(string, default: "eng")*: Primary OCR language (`eng`, `hin`, `eng+hin`).
- `engine` *(string, default: "auto")*: OCR engine selection (`auto` or `tesseract`).
- `extract_tables` *(boolean, default: true)*: Enable 2D table matrix extraction.
- `include_provenance` *(boolean, default: true)*: Include spatial bounding box provenance.
- `quality_threshold` *(float, default: 0.5)*: Quality score threshold below which OCR fallback is triggered.

### Request Example (cURL)
```bash
curl -X 'POST' \
  'https://YOUR-DOCROUTE-BACKEND.onrender.com/v1/ocr' \
  -H 'accept: application/json' \
  -F 'file=@invoice.pdf' \
  -F 'language=eng+hin' \
  -F 'extract_tables=true'
```

### Request Example (Python requests)
```python
import requests

url = "https://YOUR-DOCROUTE-BACKEND.onrender.com/v1/ocr"
files = {"file": open("invoice.pdf", "rb")}
data = {
    "language": "eng+hin",
    "extract_tables": True,
    "quality_threshold": 0.5
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Response Schema (`200 OK`)
```json
{
  "request_id": "req-9a8b7c6d",
  "document_id": "doc-f1e2d3c4",
  "status": "completed",
  "filename": "invoice.pdf",
  "total_pages": 1,
  "pages": [...],
  "text": "Extracted text content...",
  "tables": [
    {
      "table_id": "tbl-101",
      "row_count": 3,
      "column_count": 3,
      "matrix": [
        ["Item", "Qty", "Price"],
        ["Service Fee", "1", "$150.00"],
        ["Total", "1", "$150.00"]
      ]
    }
  ],
  "extraction": {
    "route": "native",
    "engines": ["pymupdf-native"]
  },
  "quality": {
    "overall_score": 0.95,
    "garbage_ratio": 0.0,
    "printable_char_ratio": 1.0,
    "ocr_confidence": 0.0
  },
  "provenance": [...]
}
```

---

## 2. Standardized Error Contract

All API errors return a structured JSON response format:

```json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "File extension '.xyz' is not supported. Use PDF, PNG, JPG, JPEG, TIFF, WEBP."
  },
  "request_id": "req-12345678"
}
```

### Standard Error Codes:
- `UNSUPPORTED_FILE_TYPE`: Invalid file extension.
- `EMPTY_FILE`: Uploaded file has 0 bytes.
- `FILE_TOO_LARGE`: Exceeds maximum configured size limit (`MAX_UPLOAD_MB`).
- `UNAUTHORIZED`: Invalid or missing API key.
- `NOT_FOUND`: Requested document ID or resource does not exist.
- `PROCESSING_FAILURE`: Internal processing error.

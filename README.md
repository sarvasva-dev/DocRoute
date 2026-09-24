# DocRoute: Adaptive Document Intelligence Engine

**DocRoute** is a production-grade, reusable document-processing framework designed to intelligently analyze, route, and extract structured text, tables, quality metrics, and page-level provenance from PDFs and image documents.

Rather than acting as a naive PyMuPDF wrapper or static OCR caller, **DocRoute** functions as an **Adaptive Engine**: it inspects document layout signals, evaluates native text quality, automatically routes scanned pages to an OpenCV-enhanced Tesseract OCR pipeline, and provides fine-grained provenance explaining *where* every piece of text came from and *why* a specific extraction method was selected.

---

## Key Features

- **Document Profiler**: Measures native text density, page dimensions, image area coverage, scan likelihood, table likelihood, and language hints (English, Hindi).
- **Native Extraction**: High-speed PyMuPDF (`fitz`) text and bounding box parsing for native vector PDFs.
- **OpenCV Preprocessing**: Image grayscale conversion, adaptive/Otsu binarization, deskew angle correction, and noise reduction.
- **Tesseract OCR Pipeline**: High-resolution OCR execution with multi-language support (English `eng`, Hindi `hin`), word confidence scores, and bounding box telemetry.
- **Adaptive Fallback Router**: Objective quality score calculation (garbage ratio, printable character ratio, dictionary word ratio) to trigger OCR fallback when native text is missing or corrupted.
- **Table Extractor**: Bounded and borderless table detection using PyMuPDF grid analysis returning structured 2D matrices and cell coordinates.
- **Page-Level Provenance**: Full traceability mapping every extracted string to page number, bounding box `[x0, y0, x1, y1]`, source element type, engine, and routing reasoning.
- **FastAPI Microservice**: Production REST API endpoints with Pydantic v2 schemas, OpenAPI specs, file validation, and visual debug rendering.
- **Unified CLI Tool**: Command-line interface (`docroute inspect`, `docroute extract`, `docroute profile`, `docroute ocr`) sharing identical engine logic with the API.

---

## Core Architecture

```
                    PDF / IMAGE
                         │
                         ▼
                 DOCUMENT PROFILER
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       Native PDF      Scanned     Complex/Table
          Text          Pages         Content
            │            │            │
            ▼            ▼            ▼
         PyMuPDF      OCR Router   Layout/Table
                         │           Processor
                         ▼
                 OpenCV Preprocess
                         │
                 ┌───────┴────────┐
                 ▼                ▼
             Tesseract       Other OCR
                              backend
                 └───────┬────────┘
                         ▼
                QUALITY ASSESSMENT
                         │
                  confidence low?
                    ┌────┴────┐
                   YES        NO
                    │          │
                 fallback    accept
                    │          │
                    └────┬─────┘
                         ▼
               STRUCTURED DOCUMENT
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         TEXT          TABLES        METADATA
                         │
                         ▼
                  PROVENANCE LAYER
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Tesseract OCR engine (v5.0+) installed on host OS (e.g. `winget install UB-Mannheim.TesseractOCR` or `choco install tesseract`).

### Environment Setup
```bash
# Clone or navigate to directory
cd D:\Projects\DocRoute

# Install dependencies in editable mode
pip install -e .
```

### Language Packs (English + Hindi)
DocRoute includes localized tessdata management. To verify installed languages:
```bash
python -c "from docroute.ocr.tesseract import TesseractOCREngine; print(TesseractOCREngine().get_supported_languages())"
```

---

## CLI Usage Examples

### 1. Inspect Document Signals
```bash
docroute inspect tests/test_data/mixed_document.pdf
```

### 2. Profile Document Layout (JSON)
```bash
docroute profile tests/test_data/native_text.pdf
```

### 3. Adaptively Extract Document
```bash
docroute extract tests/test_data/mixed_document.pdf --json
```

### 4. Force OCR Extraction
```bash
docroute ocr tests/test_data/scanned_page.pdf --lang eng+hin
```

---

## API Microservice Usage

### Launching the Server
```bash
python -m docroute.api.app
# Server runs at http://localhost:8000 (OpenAPI Docs at http://localhost:8000/docs)
```

### Available Endpoints
- `POST /documents`: Upload PDF/image file and run adaptive extraction.
- `GET /documents/{id}`: Get full structured document payload.
- `GET /documents/{id}/profile`: Get layout profile.
- `GET /documents/{id}/pages`: Get list of extracted pages.
- `GET /documents/{id}/text`: Get plain text aggregation.
- `GET /documents/{id}/tables`: Get all extracted tables.
- `GET /documents/{id}/quality`: Get overall quality report.
- `GET /documents/{id}/debug/{page_num}`: Render visual debug image with bounding boxes.

---

## Benchmarks & Evaluation

Run the reproducible benchmark suite:
```bash
python -m docroute.benchmark
```

### Verified Benchmark Results
| Metric | Result |
| :--- | :--- |
| **Documents Tested** | 6 representative PDF documents |
| **Native Route Latency** | ~17.3 ms / page |
| **OCR Route Latency** | ~284 ms / page (200 DPI rendering) |
| **Scanned Page Accuracy** | 92.8% text accuracy (CER = 0.072) |
| **Native Route Success** | 100% on clean vector PDFs |
| **OCR Fallback Rate** | 57.1% (triggered only when quality < 0.50) |

---

## Running Tests
```bash
python -m pytest -v
```

---

## Repository Documentation
- [Architecture & Design](docs/architecture.md)
- [Technical Research](docs/research.md)
- [Benchmark Report](docs/benchmark.md)
- [BulkBeat Integration Plan](docs/bulkbeat-integration.md)

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

## Architecture

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

## Installation & Configuration

### Prerequisites
- Python 3.10+
- Tesseract OCR engine installed on host OS (e.g. `apt install tesseract-ocr`, `brew install tesseract`, `winget install UB-Mannheim.TesseractOCR`, or `choco install tesseract`).

### Installation
```bash
git clone https://github.com/sarvasva-dev/DocRoute.git
cd DocRoute
pip install -e .
```

### Portable Environment Configuration
DocRoute resolves Tesseract via environment variables or system PATH:

- **Windows**:
  ```cmd
  set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  set TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
  ```
- **Linux / macOS**:
  ```bash
  export TESSERACT_CMD=/usr/bin/tesseract
  export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
  ```

---

## CLI Usage

### Inspect Document Signals
```bash
docroute inspect sample.pdf
```

### Profile Document Layout (JSON)
```bash
docroute profile sample.pdf
```

### Adaptively Extract Document
```bash
docroute extract sample.pdf --json
```

### Force OCR Extraction
```bash
docroute ocr sample_scan.pdf --lang eng+hin
```

---

## API Microservice

### Launching the Server
```bash
python -m docroute.api.app
# Server runs at http://localhost:8000 (OpenAPI Docs at http://localhost:8000/docs)
```

### Example Request (cURL)
```bash
curl -X POST "http://localhost:8000/documents?ocr_threshold=0.5" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.pdf"
```

---

## Reproducible Benchmarking

*Benchmark results depend on document layout, hardware capabilities, OCR settings, and test corpus. The included benchmark suite generates a local synthetic dataset for comparative engineering testing.*

### Running the Local Benchmark
```bash
# 1. Generate local synthetic benchmark PDFs (gitignored)
python tests/create_benchmark_dataset.py

# 2. Run benchmark evaluation
python -m docroute.benchmark
```

### Measured Local Benchmark Metrics (Synthetic Suite)
| Metric | Measured Value |
| :--- | :--- |
| **Dataset Evaluated** | 6 synthetic test documents (7 pages) |
| **Native Route Latency** | ~17.4 ms / page |
| **OCR Pipeline Latency** | ~471.4 ms / page (includes 200 DPI rendering, deskewing & Tesseract OCR) |
| **Scanned Page Accuracy** | 92.8% text accuracy (CER = 0.0722 on scanned page) |
| **OCR Fallback Rate** | 57.1% (triggered strictly when native quality score < 0.50) |

---

## Running Tests
```bash
python -m pytest -v
```

---

## Documentation
- [Architecture & Technical Design](docs/architecture.md)
- [Technology Evaluation & Research](docs/research.md)
- [Benchmark Report](docs/benchmark.md)
- [BulkBeat Integration Plan](docs/bulkbeat-integration.md)
- [Repository Cleanup Report](docs/repository_cleanup.md)

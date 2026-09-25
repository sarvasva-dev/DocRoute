# DocRoute: Adaptive Document Intelligence Engine

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Project-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://rzp.io/rzp/0e1N1Vb)

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
- **Interactive Web Dashboard**: Glassmorphism UI mounted at `/dashboard/` for file uploads, bounding box canvas overlays, table matrix inspectors, scan likelihood gauges, quality reports, and interactive API code generators.
- **Render.com Cloud Ready**: Native `Dockerfile` and `render.yaml` infrastructure-as-code for zero-downtime deployment on Render.
- **Unified CLI Tool**: Command-line interface (`docroute inspect`, `docroute extract`, `docroute profile`, `docroute ocr`) sharing identical engine logic with the API.

---

## Web Dashboard & Interactive Inspector

DocRoute includes a standalone, high-performance web interface mounted directly at `/dashboard/` when running the microservice.

### Key Web Features:
1. **Drag-and-Drop Uploader**: Upload PDF documents or images with customizable scan likelihood thresholds, OCR language engines (`eng`, `hin`, `eng+hin`), force OCR toggles, and table extraction controls.
2. **Spatial Bounding Box Canvas**: Renders uploaded pages onto an interactive HTML5 canvas with color-coded bounding box overlays (blue = vector native, green = OCR, purple = table grid) and real-time hover tooltips.
3. **Visual Debug Stream**: Live streams server-side annotated debug overlay images from `/documents/{id}/debug/{page_num}`.
4. **Table Matrix Grid Inspector**: Renders extracted 2D table matrices into formatted HTML grids with 1-click **Copy to JSON** and **Copy to CSV** export functions.
5. **Quality & Provenance Stream**: Displays detailed quality metrics (`ocr_confidence`, `formatting_density`, `garbage_ratio`) alongside a line-by-line spatial provenance log table.
6. **API Code Generator**: Interactive code snippet switcher providing ready-to-copy request code in **cURL**, **Python (requests)**, **JavaScript (fetch)**, and **Node.js (axios)**.

---

## Render.com Cloud Deployment

DocRoute is fully prepared for containerized cloud deployment on **Render.com** using Docker with preinstalled Tesseract OCR (English + Hindi) and system OpenCV dependencies.

### Option 1: Render Infrastructure-as-Code (Recommended)
1. Fork or push your code to your GitHub repository: `https://github.com/sarvasva-dev/DocRoute`.
2. In your Render Dashboard, select **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml` and provision the Web Service.

### Option 2: Manual Render Web Service Setup
1. Create a **New Web Service** on Render.
2. Connect your GitHub repository: `https://github.com/sarvasva-dev/DocRoute`.
3. Select Environment: **Docker**.
4. Set **Dockerfile Path**: `./Dockerfile`.
5. Set Environment Variables:
   - `PORT`: `8000`
   - `TESSERACT_CMD`: `/usr/bin/tesseract`
6. Click **Deploy Web Service**.

---

## API Microservice & Endpoints

### Launching Locally
```bash
python -m docroute.api.app
# Server runs at http://localhost:8000
# Web Dashboard: http://localhost:8000/dashboard/
# OpenAPI Specs:  http://localhost:8000/docs
```

### Exposed API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/documents` | Upload & process document (`.pdf`, `.png`, `.jpg`, `.tiff`, `.webp`). Returns `StructuredDocument`. |
| `GET` | `/documents/{id}` | Retrieve full structured document model payload by ID. |
| `GET` | `/documents/{id}/profile` | Retrieve layout profile, native text density, and scan likelihood score. |
| `GET` | `/documents/{id}/pages` | Retrieve list of page extractions with bounding boxes and line tokens. |
| `GET` | `/documents/{id}/text` | Retrieve aggregated plain text across all document pages. |
| `GET` | `/documents/{id}/tables` | Retrieve all extracted 2D table matrices across document pages. |
| `GET` | `/documents/{id}/quality` | Retrieve document extraction quality assessment metrics. |
| `GET` | `/documents/{id}/debug/{page_num}` | Download/stream visual debug annotated page overlay PNG image. |

### Example API Request (cURL)
```bash
curl -X 'POST' \
  'http://localhost:8000/documents?ocr_threshold=0.5&force_ocr=false&language=eng%2Bhin&extract_tables=true' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.pdf'
```

---

## Docker Local Execution

You can build and run DocRoute locally in Docker using the included `Dockerfile`:

```bash
# Build Docker image
docker build -t docroute-engine .

# Run Docker container
docker run -d -p 8000:8000 --name docroute docroute-engine

# Access Dashboard at http://localhost:8000/dashboard/
```

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

---

## ☕ Support & Sponsorship

If **DocRoute** has helped your project or saves you money on commercial document OCR APIs, please consider supporting the project's development and hosting costs!

[![Support & Buy Me a Coffee](https://img.shields.io/badge/☕_Buy_Me_a_Coffee-Support_DocRoute-f59e0b?style=for-the-badge&logoColor=white)](https://rzp.io/rzp/0e1N1Vb)

👉 **[Click Here to Support / Buy Me a Coffee](https://rzp.io/rzp/0e1N1Vb)** (`https://rzp.io/rzp/0e1N1Vb`)


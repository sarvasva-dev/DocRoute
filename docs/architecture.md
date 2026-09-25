# DocRoute Engine Architecture & Design

**DocRoute** is an open-source adaptive document intelligence engine and REST API designed as a developer-friendly alternative to commercial document AI APIs (such as Google Cloud Vision and AWS Textract).

---

## 1. High-Level Architectural Pipeline

```
                       PDF / IMAGE DOCUMENT
                                │
                                ▼
                       DOCUMENT PROFILER
             (Text Density, Scan Likelihood, DPI)
                                │
                                ▼
                   ADAPTIVE ROUTING DECISION
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
       NATIVE VECTOR        OCR ROUTE         HYBRID ROUTE
       (PyMuPDF Text)   (OpenCV + Tesseract)   (Combined)
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                                ▼
                        TABLE EXTRACTOR
                 (Grid Bounding & Cell Parsing)
                                │
                                ▼
                       QUALITY ASSESSMENT
              (Garbage Ratio, Printable Ratio, CER)
                                │
                                ▼
                        PROVENANCE STREAM
                (Spatial BBoxes [x0,y0,x1,y1])
                                │
                                ▼
                     STRUCTURED JSON PAYLOAD
```

---

## 2. Core Components

### A. Document Profiler (`docroute/core/profiler.py`)
Analyzes raw file layout before extraction:
- **Native Text Density**: Character count per page unit area.
- **Scan Likelihood Score**: `0.0` (pure vector digital PDF) to `1.0` (scanned bitmap image).
- **Language Hints**: Detects English `eng` and Hindi `hin` character ranges.

### B. Adaptive Routing Decision (`docroute/routing/router.py`)
- Evaluates native text quality against the configured `quality_threshold` (default `0.5`).
- If native text quality >= threshold: Routes to **Native Vector Extraction** (`pymupdf-native`). Latency: ~17ms/page.
- If native text quality < threshold (or forced OCR): Routes to **OpenCV + Tesseract OCR Pipeline**. Latency: ~470ms/page.

### C. OpenCV Image Preprocessing (`docroute/ocr/preprocessing.py`)
- Grayscale conversion.
- Otsu adaptive binarization.
- Deskew angle calculation & rotation correction.
- Gaussian noise reduction.

### D. Tesseract OCR Engine (`docroute/ocr/tesseract.py`)
- Multi-language support (`eng`, `hin`, `eng+hin`).
- Word-level confidence score extraction.
- Spatial bounding box coordinate generation.

### E. Table Extractor (`docroute/extractors/tables.py`)
- Detects horizontal and vertical line intersections.
- Extracts 2D structured table matrices with headers and cell coordinates.

### F. Spatial Provenance Tracking (`docroute/models/provenance.py`)
- Maps every string snippet to page number, bounding box `[x0, y0, x1, y1]`, source engine, confidence level, and routing reasoning.

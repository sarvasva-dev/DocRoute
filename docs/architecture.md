# DocRoute Core Architecture & Design Specification

## Overview
DocRoute is structured as a modular Python framework designed for production deployment, microservice execution, and CLI batch operations. It solves the core document processing dilemma: *How should this document be read, and why was this extraction method selected?*

---

## Component Architecture

### 1. Document Profiler (`docroute.core.profiler`)
- Inspects input PDF catalog/metadata and page geometry.
- Calculates native character count, surface area density (characters per 1000 square points), embedded image count, and image area coverage ratio.
- Evaluates `scan_likelihood` (0.0 to 1.0) and `table_likelihood` (0.0 to 1.0).
- Detects Devanagari character ranges to provide language hints (`hin`).

### 2. Native Extractor (`docroute.extractors.native`)
- Uses PyMuPDF (`fitz`) to extract block-level text elements (`page.get_text("blocks")`).
- Extracts exact coordinates `[x0, y0, x1, y1]` for each text block.
- Assigns 1.0 confidence for native vector text.

### 3. OCR Pipeline (`docroute.ocr`)
- **Image Preprocessor (`docroute.ocr.preprocessing`)**: Converts rendered page image buffers to OpenCV array, applies Otsu binarization, calculates document skew angle via contour bounding boxes, and performs affine rotation correction.
- **Tesseract Engine (`docroute.ocr.tesseract`)**: Executes PyTesseract with explicit `TESSDATA_PREFIX` management, supports English (`eng`) and Hindi (`hin`), returns text strings, word-level confidence metrics, and word bounding boxes.

### 4. Adaptive OCR Fallback Router (`docroute.routing`)
- **Quality Assessor (`docroute.routing.quality`)**: Calculates garbage character ratio (unprintable / noise symbols), printable character ratio, and dictionary word ratio.
- **OCR Router (`docroute.routing.router`)**: Compares native quality score against a configurable threshold (default `0.50`). If native text density is minimal (<15 chars) or quality score is below threshold, OCR fallback is invoked with detailed human-readable reasoning.

### 5. Table Extractor (`docroute.extractors.tables`)
- Uses PyMuPDF's `find_tables()` TableFinder API.
- Extracts header strings, 2D matrix rows, cell bounding boxes, and column/row spans.

### 6. Page-Level Provenance Layer (`docroute.provenance`)
- Every extracted string or word is recorded in a `ProvenanceRecord`.
- Stores `record_id`, `document_id`, `page_number`, `extraction_method`, `engine`, `bbox`, `text_snippet`, `confidence`, `source_element`, and `routing_reasoning`.

### 7. Security Controls (`docroute.api.routes`)
- Path traversal prevention: sanitizes filenames using `os.path.basename` and rejects relative paths (`..`, `/`, `\`).
- File size enforcement: rejects uploads exceeding 50 MB.
- Temporary file isolation: writes uploads to isolated temporary directories (`tempfile.mkdtemp`) with cleanup.

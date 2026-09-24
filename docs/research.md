# Technical Research & Evaluation: Document Processing Engine

## Executive Overview
This document evaluates candidate document processing, optical character recognition (OCR), layout analysis, and API frameworks for **DocRoute: Adaptive Document Intelligence Engine**. Each technology is evaluated based on documented upstream capabilities vs. our actual implemented features within DocRoute.

---

## 1. PyMuPDF (`fitz`)

* **Purpose**: Primary engine for native PDF parsing, text extraction, page rendering, layout inspection, and table bounding box discovery.
* **Current Capability**: PyMuPDF 1.27+ provides high-speed C-level bindings to MuPDF. Supports native text extraction, font attributes, character position bounding boxes, image extraction, page rendering to pixmaps/images (DPI control), document metadata extraction, and primitive table detection (`page.find_tables()`).
* **Relevant API**:
  * `fitz.open(file_path)`
  * `page.get_text("text" | "blocks" | "dict" | "words")`
  * `page.get_pixmap(dpi=200)`
  * `page.find_tables()`
* **License**: AGPL-3.0 / Commercial dual-license.
* **Limitations**: Scanned PDFs with rasterized images return empty/minimal text strings. Complex multi-column or borderless tables may require heuristic alignment logic.
* **Why Used**: Fast C-based text extraction (up to 10-100x faster than pure Python parsers), low memory footprint, excellent rendering capabilities for downstream OCR input generation.
* **Capability Comparison**:
  * *Documented Capability*: Full PDF/XPS/EPUB rendering, vector drawing analysis, PDF editing, text search, table extraction.
  * *Our Implemented Feature*: Page-by-page native text extraction, metadata parsing, high-resolution (DPI) page rendering for OCR routing, and page geometry/density profiling.

---

## 2. PyMuPDF4LLM

* **Purpose**: Extends PyMuPDF to convert PDF documents into structured Markdown/JSON optimized for LLM RAG pipelines.
* **Current Capability**: Layout-aware markdown conversion, header identification, multi-column reading order detection, table markdown/HTML rendering (`table_output="html"`), and layout chunking.
* **Relevant API**: `pymupdf4llm.to_markdown()`, `pymupdf4llm.to_json()`
* **License**: AGPL-3.0 / Commercial.
* **Limitations**: Requires clean text layer; scanned PDFs still depend on external OCR integration. Heavy layout heuristic tuning needed for complex non-standard forms.
* **Why Used / Evaluation**: Evaluated as an optional output formatter. DocRoute core uses PyMuPDF directly to maintain fine-grained page provenance, bounding box metadata, and custom routing scores.
* **Capability Comparison**:
  * *Documented Capability*: RAG-ready markdown extraction with GNN layout analysis.
  * *Our Implemented Feature*: Direct integration evaluated; custom structured JSON and provenance models in DocRoute provide finer page/element coordinate mapping.

---

## 3. Tesseract OCR (`pytesseract`)

* **Purpose**: Primary Optical Character Recognition (OCR) engine for scanned documents, image-heavy PDFs, and low-density native text fallback.
* **Current Capability**: Open-source LSTM-based OCR engine supporting 100+ languages. `pytesseract` wraps the Tesseract binary to return text strings, detailed word-level bounding boxes, confidence scores, and HOCR output.
* **Relevant API**:
  * `pytesseract.image_to_string(image, lang="eng+hin", config="--psm 6")`
  * `pytesseract.image_to_data(image, output_type=Output.DICT)`
* **License**: Apache 2.0.
* **Limitations**: CPU-intensive on high-DPI images; requires preprocessed (deskewed, contrast-adjusted, binarized) images for optimal accuracy on noisy scans. Requires installed language data packs (`tessdata`).
* **Why Used**: Free, open-source, robust offline operation, wide language support (English, Hindi), fine-grained word confidence and bounding box telemetry.
* **Capability Comparison**:
  * *Documented Capability*: Multi-language OCR, page segmentation modes (PSM), orientation/script detection (OSD), word bounding boxes and confidence.
  * *Our Implemented Feature*: Integrated in OCR pipeline with OpenCV preprocessed image input, fallback routing based on quality scores, multi-language support (English/Hindi), and confidence extraction.

---

## 4. OpenCV (`cv2`)

* **Purpose**: Image preprocessing pipeline to optimize document scan quality before passing image buffers to Tesseract OCR.
* **Current Capability**: Computer vision operations including grayscale conversion, Adaptive/Otsu thresholding, Gaussian/Bilateral denoising, deskewing via contour/minAreaRect detection, morphological operations, and image resizing.
* **Relevant API**:
  * `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`
  * `cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)`
  * `cv2.fastNlMeansDenoising()`
  * `cv2.getRotationMatrix2D()`, `cv2.warpAffine()`
* **License**: Apache 2.0.
* **Limitations**: Incorrect deskew or hyper-aggressive thresholding can distort fine text strokes or small fonts.
* **Why Used**: Provides deterministic, ultra-fast C++ image enhancement that significantly reduces character error rate (CER) on scanned and degraded documents.
* **Capability Comparison**:
  * *Documented Capability*: Full computer vision suite (deep learning, feature matching, image transforms).
  * *Our Implemented Feature*: Targeted document preprocessing module: Grayscale, Otsu/Adaptive Thresholding, Gaussian Denoising, Deskew Angle Correction, and Rescaling.

---

## 5. PaddleOCR

* **Purpose**: Deep-learning based OCR engine (PP-OCR series) supporting multi-angle text detection and recognition.
* **Current Capability**: State-of-the-art accuracy on complex background documents, rotated text, and multi-lingual layout analysis.
* **Relevant API**: `PaddleOCR(use_angle_cls=True, lang='en')`
* **License**: Apache 2.0.
* **Limitations**: High memory overhead (requires PyTorch/PaddlePaddle runtime), heavy initial model download (~100MB+), slower startup on CPU-only edge/VPS environments.
* **Why Used / Why NOT Primary**: Useful as an alternative secondary OCR backend. Not chosen as primary due to heavyweight memory/dependency requirements for lightweight deployments, but architecture allows routing to it.
* **Capability Comparison**:
  * *Documented Capability*: Deep-learning text detection (DBNet) & recognition (SVTR), layout parsing, table structure extraction (PP-Structure).
  * *Our Implemented Feature*: Evaluated legacy usage in project inventory; optional backend interface provided in DocRoute routing layer.

---

## 6. Docling (IBM Research)

* **Purpose**: AI-powered document layout analysis and table structure parsing framework.
* **Current Capability**: Uses DocLayNet (layout) and TableFormer (table structure) deep models to convert PDFs, DOCX, PPTX into structured Markdown and JSON.
* **Relevant API**: `DocumentConverter().convert(doc_path)`
* **License**: MIT License.
* **Limitations**: Requires ML model execution environment (PyTorch/Transformers dependencies), high CPU/GPU memory usage during model inference.
* **Why Used / Why NOT Primary**: Evaluated for advanced table parsing. Kept as a reference architectural pattern while DocRoute core remains lightweight, deterministic, and fast without mandatory heavy GPU dependencies.
* **Capability Comparison**:
  * *Documented Capability*: ML-driven layout parsing and multi-format document conversion.
  * *Our Implemented Feature*: Evaluated in technical review; layout concepts adapted into DocRoute's rule-based document profiler and table extraction pipeline.

---

## 7. FastAPI

* **Purpose**: High-performance REST API web framework for exposing document ingestion, profiling, extraction, and quality reporting endpoints.
* **Current Capability**: Asynchronous request handling, auto-generated OpenAPI (Swagger) specs, Pydantic integration, streaming responses, background task processing.
* **Relevant API**: `FastAPI()`, `APIRouter()`, `UploadFile`, `File()`, `HTTPException`
* **License**: MIT License.
* **Limitations**: Requires ASGI server (`uvicorn`) for execution.
* **Why Used**: Modern standard for Python microservices, native async support, strict data contract enforcement with Pydantic.
* **Capability Comparison**:
  * *Documented Capability*: Asynchronous web framework, WebSocket support, OAuth2 security, automatic OpenAPI generation.
  * *Our Implemented Feature*: Complete REST API endpoints (`/documents`, `/documents/{id}/profile`, `/documents/{id}/pages`, `/documents/{id}/text`, `/documents/{id}/tables`, `/documents/{id}/quality`) with upload handling, validation, and visual debug response formats.

---

## 8. Pydantic (v2)

* **Purpose**: Data validation, schema definition, and type safety across DocRoute's core objects, API models, and JSON outputs.
* **Current Capability**: Rust-backed core (Pydantic v2), high-speed serialization/deserialization, strict field validation, custom type validators, JSON schema generation.
* **Relevant API**: `BaseModel`, `Field`, `model_validator`, `ConfigDict`
* **License**: MIT License.
* **Limitations**: Strict type enforcement requires explicit handling of optional or fallback fields.
* **Why Used**: Ensures production-grade data integrity across document profiles, page extractions, quality scores, table models, and provenance payloads.
* **Capability Comparison**:
  * *Documented Capability*: Type validation, settings management, JSON schema generation, custom serialization.
  * *Our Implemented Feature*: Domain models for `DocumentProfile`, `PageExtraction`, `TableData`, `ProvenanceRecord`, `QualityScore`, and `StructuredDocument`.

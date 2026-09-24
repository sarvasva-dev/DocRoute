# BulkBeat TV / NSE Monitor Integration Audit & Plan

## Overview
This document analyzes the existing PDF extraction logic in **BulkBeat TV / NSE Monitor** (`d:/Projects/nse2/nse_monitor/pdf_processor.py`) and defines an integration plan to adopt **DocRoute** as its document intelligence engine without breaking existing scraper functionality.

---

## 1. Existing BulkBeat Logic vs DocRoute Equivalent

| Component | Existing BulkBeat Logic (`pdf_processor.py`) | DocRoute Engine Equivalent |
| :--- | :--- | :--- |
| **PDF Download & Session** | Retries, User-Agent rotation, NSE session headers (`download_pdf`) | **Project Specific**: Stays in BulkBeat NSE Monitor |
| **Native Extraction** | `fitz.open(pdf_path)` + loop `page.get_text()` | `NativePDFExtractor` with block coordinates and bounding box tracking |
| **OCR Fallback Trigger** | Hardcoded length threshold (`len(text) < 150`) | `OCRRouter` with composite quality scoring (density, garbage ratio, dictionary words) |
| **OCR Execution** | `fitz` pixmap at 200 DPI -> `pytesseract.image_to_string` | `OCRExtractor` with OpenCV deskew/binarization + `TesseractOCREngine` |
| **Concurrency Control** | `threading.Lock()` RAM lock for 1GB VPS | Integrated RAM safety controls & configurable DPI settings |
| **Table Extraction** | None | `TableExtractor` (PyMuPDF `find_tables` matrix parsing) |
| **Provenance Tracking** | None | Full page & element bounding box traceability |

---

## 2. What Should Be Reused vs What Stays Project-Specific

### Keep Project-Specific in BulkBeat
- **NSE HTTP Session & UA Jitter**: Downloading corporate PDFs from `nsearchives.nseindia.com` requires custom header rotation, session cookie refresh, and proxy bypass rules. This stays in BulkBeat.

### Reusable with DocRoute Framework
- **Document Profiling & Quality Scoring**: Replaces naive `len(text) < 150` check with DocRoute's objective quality score.
- **Enhanced OCR Pipeline**: Replaces raw Tesseract call with OpenCV deskewing and adaptive binarization to increase OCR accuracy on noisy corporate filings.
- **Table Extraction**: Extracts financial balance sheets and announcement tables directly into structured JSON.

---

## 3. BulkBeat Integration Adapter Example

To integrate DocRoute into BulkBeat without modifying existing code, an adapter class can be added to BulkBeat:

```python
# BulkBeat Integration Adapter Example (docroute_adapter.py)
from nse_monitor.pdf_processor import PDFProcessor
from docroute.core.engine import DocRouteEngine
from docroute.models.api import ProcessingOptions

class DocRoutePDFProcessorAdapter(PDFProcessor):
    """Adapter class extending BulkBeat's PDFProcessor to use DocRoute engine."""

    def __init__(self):
        super().__init__()
        self.docroute_engine = DocRouteEngine(
            options=ProcessingOptions(ocr_threshold=0.5, extract_tables=True)
        )

    def extract_text(self, pdf_path: str) -> str:
        """Overrides extract_text to use DocRoute adaptive processing."""
        if not pdf_path or not os.path.exists(pdf_path):
            return ""

        structured_doc = self.docroute_engine.process_document(pdf_path)
        # Combine extracted page texts
        full_text = "\n\n".join(p.text for p in structured_doc.pages)
        return full_text
```

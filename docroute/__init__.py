"""DocRoute: Adaptive Document Intelligence Engine with Akshar Vision."""
from docroute.core.engine import DocRouteEngine, ENGINE_VERSION
from docroute.models.api import ProcessingOptions, DocumentUploadResponse, ErrorResponse
from docroute.models.document import StructuredDocument

__version__ = ENGINE_VERSION

def extract(
    file_path: str,
    vision: str = "akshar",
    force_ocr: bool = False,
    extract_tables: bool = True,
    ocr_threshold: float = 0.5,
    language: str = "eng",
    **kwargs
) -> StructuredDocument:
    """Convenience top-level extraction API for DocRoute.
    
    Args:
        file_path: Path to PDF or image document
        vision: Vision OCR engine ("akshar" [default], "mirage", "tesseract")
        force_ocr: Force OCR on all pages
        extract_tables: Recover 2D table structures
        ocr_threshold: Confidence/quality threshold
        language: OCR language
        
    Returns:
        StructuredDocument containing page text, tables, quality, and provenance.
    """
    opts = ProcessingOptions(
        vision=vision,
        force_ocr=force_ocr,
        extract_tables=extract_tables,
        ocr_threshold=ocr_threshold,
        language=language,
        **kwargs
    )
    engine = DocRouteEngine(options=opts)
    return engine.process_document(file_path)

__all__ = [
    "DocRouteEngine",
    "ProcessingOptions",
    "StructuredDocument",
    "extract",
    "__version__",
]

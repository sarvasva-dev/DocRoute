from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from docroute.models.document import StructuredDocument
from docroute.models.profile import DocumentProfile
from docroute.models.extraction import PageExtraction
from docroute.models.table import TableData
from docroute.models.quality import QualityScore

class ProcessingOptions(BaseModel):
    """Configuration options for processing requests."""
    ocr_threshold: float = Field(0.5, description="Quality score threshold below which OCR is invoked")
    force_ocr: bool = Field(False, description="Force OCR execution on all pages regardless of quality")
    language: str = Field("eng", description="Primary OCR language (e.g. eng, hin, eng+hin)")
    extract_tables: bool = Field(True, description="Enable table extraction")
    visual_debug: bool = Field(False, description="Enable visual debug image generation")

class DocumentUploadResponse(BaseModel):
    """Response returned upon document upload & processing initiation."""
    document_id: str
    filename: str
    status: str
    page_count: int
    profile: DocumentProfile

class ErrorResponse(BaseModel):
    """Standardized structured error response."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

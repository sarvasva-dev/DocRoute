from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PageProfile(BaseModel):
    """Profile signals for an individual page."""
    page_number: int = Field(..., description="1-indexed page number")
    width: float = Field(..., description="Page width in points")
    height: float = Field(..., description="Page height in points")
    native_char_count: int = Field(0, description="Total characters extracted natively")
    text_density: float = Field(0.0, description="Characters per 1000 square points")
    image_count: int = Field(0, description="Number of embedded images on page")
    image_area_ratio: float = Field(0.0, description="Ratio of page area covered by raster images")
    scan_likelihood: float = Field(0.0, description="Likelihood page is a scanned image (0.0 to 1.0)")
    table_likelihood: float = Field(0.0, description="Likelihood page contains structured tables (0.0 to 1.0)")
    language_hints: List[str] = Field(default_factory=list, description="Detected or hint language codes")
    quality_signals: Dict[str, Any] = Field(default_factory=dict, description="Raw extraction quality indicators")

class DocumentProfile(BaseModel):
    """Aggregate profile metrics for an entire document."""
    document_id: str = Field(..., description="Unique identifier or filename")
    page_count: int = Field(..., description="Total pages in document")
    avg_text_density: float = Field(0.0, description="Average character density across pages")
    is_scanned_pdf: bool = Field(False, description="True if document appears fully or predominantly scanned")
    is_native_pdf: bool = Field(True, description="True if document contains clean vector text layers")
    is_mixed_pdf: bool = Field(False, description="True if document has mixed native and scanned pages")
    is_image_heavy: bool = Field(False, description="True if document is image dominated")
    is_table_heavy: bool = Field(False, description="True if document contains multiple tables")
    primary_language: str = Field("eng", description="Primary detected language code")
    pdf_metadata: Dict[str, Any] = Field(default_factory=dict, description="PDF header/catalog metadata")
    pages: List[PageProfile] = Field(default_factory=list, description="Page-level profiles")

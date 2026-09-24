from typing import List, Optional
from pydantic import BaseModel, Field

class ProvenanceRecord(BaseModel):
    """Traceability record explaining where an extracted element came from and why."""
    record_id: str = Field(..., description="Unique record identifier")
    document_id: str = Field(..., description="Document identifier")
    page_number: int = Field(..., description="1-indexed page number")
    extraction_method: str = Field(..., description="Extraction route: native, ocr, hybrid")
    engine: str = Field(..., description="Specific engine used (e.g. pymupdf-native, opencv+tesseract)")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x0, y0, x1, y1] in points/pixels")
    text_snippet: str = Field("", description="Truncated snippet of extracted text")
    confidence: Optional[float] = Field(None, description="Confidence score if available (0.0 to 1.0 or 0-100)")
    source_element: str = Field("text_block", description="Source element type: text_block, ocr_word, table_cell")
    routing_reasoning: str = Field("", description="Explanation of why this extraction method was selected")

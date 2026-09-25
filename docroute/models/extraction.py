from typing import List
from pydantic import BaseModel, Field
from docroute.models.quality import QualityScore
from docroute.models.table import TableData
from docroute.models.provenance import ProvenanceRecord

class PageExtraction(BaseModel):
    """Extracted content for a single document page."""
    page_number: int = Field(..., description="1-indexed page number")
    width: float = Field(612.0, description="Page width in points/pixels")
    height: float = Field(792.0, description="Page height in points/pixels")
    text: str = Field("", description="Full text extracted for page")
    extraction_method: str = Field(..., description="Extraction method used: native | ocr | hybrid")
    quality: QualityScore = Field(..., description="Page quality score and routing metrics")
    tables: List[TableData] = Field(default_factory=list, description="Extracted tables on page")
    provenance: List[ProvenanceRecord] = Field(default_factory=list, description="Page element provenance list")


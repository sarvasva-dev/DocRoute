from typing import List, Dict, Any
from pydantic import BaseModel, Field
from docroute.models.extraction import PageExtraction
from docroute.models.quality import QualityScore

class StructuredDocument(BaseModel):
    """Complete structured document response payload."""
    document_id: str = Field(..., description="Unique document ID or filename")
    pages: List[PageExtraction] = Field(default_factory=list, description="Extracted pages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata catalog")
    overall_quality: QualityScore = Field(..., description="Overall document quality summary")
    engine_version: str = Field("1.0.0", description="DocRoute engine version string")

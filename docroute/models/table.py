from typing import List, Optional
from pydantic import BaseModel, Field

class TableCell(BaseModel):
    """Represents an individual table cell."""
    row: int = Field(..., description="0-indexed row index")
    col: int = Field(..., description="0-indexed column index")
    rowspan: int = Field(1, description="Row span count")
    colspan: int = Field(1, description="Column span count")
    text: str = Field("", description="Cell text content")
    bbox: Optional[List[float]] = Field(None, description="Cell bounding box [x0, y0, x1, y1]")
    confidence: Optional[float] = Field(None, description="Extraction confidence score")

class TableData(BaseModel):
    """Structured table representation."""
    table_id: str = Field(..., description="Unique table ID")
    page_number: int = Field(..., description="1-indexed page number where table resides")
    num_rows: int = Field(..., description="Total rows count")
    num_cols: int = Field(..., description="Total columns count")
    headers: List[str] = Field(default_factory=list, description="Extracted column header strings")
    rows: List[List[str]] = Field(default_factory=list, description="2D matrix of row cell texts")
    cells: List[TableCell] = Field(default_factory=list, description="Detailed cell list with coordinates")
    bbox: Optional[List[float]] = Field(None, description="Table bounding box [x0, y0, x1, y1]")
    extraction_method: str = Field("pymupdf-grid", description="Method used: pymupdf-grid, layout-heuristics")
    confidence: float = Field(1.0, description="Overall table extraction confidence")

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class QualityScore(BaseModel):
    """Extraction quality score metrics and fallback routing decision."""
    native_text_density: float = Field(0.0, description="Native character count per page area ratio")
    garbage_ratio: float = Field(0.0, description="Ratio of non-printable or noisy symbol characters")
    printable_char_ratio: float = Field(1.0, description="Ratio of standard alphanumeric/punctuation chars")
    dictionary_word_ratio: float = Field(0.0, description="Ratio of valid dictionary words detected")
    ocr_confidence: Optional[float] = Field(None, description="Average OCR confidence score if OCR was run (0-100)")
    overall_score: float = Field(0.0, description="Calculated composite quality score (0.0 to 1.0)")
    threshold_applied: float = Field(0.5, description="Quality threshold used for routing decision")
    extraction_route: str = Field("native", description="Selected route: native, ocr, hybrid, fallback")
    fallback_triggered: bool = Field(False, description="True if OCR fallback was invoked")
    reasoning: str = Field("", description="Human readable explanation of route choice")

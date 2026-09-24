"""Page-level Bounding Box and Extraction Provenance Tracker."""
import logging
from typing import List, Dict, Any, Optional
from docroute.models.provenance import ProvenanceRecord

logger = logging.getLogger(__name__)

class ProvenanceTracker:
    """Manages element origin, coordinate bounding boxes, and routing justifications."""

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.records: List[ProvenanceRecord] = []

    def add_record(self, record: ProvenanceRecord) -> None:
        """Appends a new provenance record."""
        self.records.append(record)

    def add_records(self, records: List[ProvenanceRecord]) -> None:
        """Appends multiple provenance records."""
        self.records.extend(records)

    def get_records_for_page(self, page_number: int) -> List[ProvenanceRecord]:
        """Returns provenance records for a specific page."""
        return [r for r in self.records if r.page_number == page_number]

    def query_text_origin(self, query_snippet: str) -> List[Dict[str, Any]]:
        """Answers: 'Where did this extracted text come from and why was this extraction method selected?'
        
        Args:
            query_snippet: Text fragment to locate
            
        Returns:
            List of structured origin explanations
        """
        results = []
        query_lower = query_snippet.lower()

        for rec in self.records:
            if query_lower in rec.text_snippet.lower():
                results.append({
                    "record_id": rec.record_id,
                    "page_number": rec.page_number,
                    "extraction_method": rec.extraction_method,
                    "engine": rec.engine,
                    "bounding_box": rec.bbox,
                    "confidence": rec.confidence,
                    "text_snippet": rec.text_snippet,
                    "routing_justification": rec.routing_reasoning,
                    "source_explanation": (
                        f"Extracted on page {rec.page_number} via {rec.engine} ({rec.extraction_method} route). "
                        f"Bounding box: {rec.bbox}. Justification: {rec.routing_reasoning}"
                    )
                })

        return results

"""Unit tests for Provenance Tracking."""
import pytest
from docroute.provenance.tracker import ProvenanceTracker
from docroute.models.provenance import ProvenanceRecord

def test_provenance_tracker():
    tracker = ProvenanceTracker(document_id="test.pdf")
    rec = ProvenanceRecord(
        record_id="rec-1",
        document_id="test.pdf",
        page_number=1,
        extraction_method="native",
        engine="pymupdf-native",
        bbox=[50.0, 70.0, 200.0, 100.0],
        text_snippet="DocRoute Engine",
        confidence=1.0,
        source_element="text_block",
        routing_reasoning="High text density"
    )
    tracker.add_record(rec)

    records = tracker.get_records_for_page(1)
    assert len(records) == 1
    assert records[0].record_id == "rec-1"

    query_res = tracker.query_text_origin("DocRoute")
    assert len(query_res) == 1
    assert query_res[0]["page_number"] == 1
    assert "pymupdf-native" in query_res[0]["engine"]
    assert "High text density" in query_res[0]["routing_justification"]

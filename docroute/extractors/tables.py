"""Table Extractor using PyMuPDF and Grid Heuristics."""
import logging
import uuid
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF

from docroute.models.table import TableData, TableCell

logger = logging.getLogger(__name__)

class TableExtractor:
    """Extracts structured tables from PDF pages using PyMuPDF layout analysis."""

    def extract_tables_from_page(self, file_path: str, page_number: int) -> List[TableData]:
        """Finds and extracts structured tables on a target PDF page.
        
        Args:
            file_path: Path to PDF file
            page_number: 1-indexed page number
            
        Returns:
            List of extracted TableData models
        """
        extracted_tables: List[TableData] = []
        page_idx = page_number - 1

        if not file_path.lower().endswith(".pdf"):
            return extracted_tables

        try:
            with fitz.open(file_path) as doc:
                if page_idx < 0 or page_idx >= len(doc):
                    return extracted_tables
                
                page = doc[page_idx]
                tabs = page.find_tables()  # PyMuPDF TableFinder object
                tables_list = tabs.tables if hasattr(tabs, "tables") else []

                for idx, tab in enumerate(tables_list):
                    table_bbox = [float(b) for b in tab.bbox] if hasattr(tab, "bbox") else None
                    extract_matrix = tab.extract()  # 2D list of strings

                    if not extract_matrix or len(extract_matrix) == 0:
                        continue

                    # Treat first row as headers if strings are clean
                    headers = [str(c or "").strip() for c in extract_matrix[0]]
                    rows = []
                    for row in extract_matrix[1:]:
                        rows.append([str(c or "").strip() for c in row])

                    cells: List[TableCell] = []
                    for r_idx, row in enumerate(extract_matrix):
                        for c_idx, cell_val in enumerate(row):
                            val_str = str(cell_val or "").strip()
                            cells.append(TableCell(
                                row=r_idx,
                                col=c_idx,
                                rowspan=1,
                                colspan=1,
                                text=val_str,
                                bbox=None,
                                confidence=1.0
                            ))

                    num_rows = len(extract_matrix)
                    num_cols = max(len(r) for r in extract_matrix) if extract_matrix else 0

                    table_model = TableData(
                        table_id=f"tab-p{page_number}-{idx+1}-{uuid.uuid4().hex[:6]}",
                        page_number=page_number,
                        num_rows=num_rows,
                        num_cols=num_cols,
                        headers=headers,
                        rows=rows,
                        cells=cells,
                        bbox=table_bbox,
                        extraction_method="pymupdf-findtables",
                        confidence=0.95
                    )
                    extracted_tables.append(table_model)

            return extracted_tables

        except Exception as e:
            logger.warning(f"Table extraction error on {file_path} page {page_number}: {e}")
            return []

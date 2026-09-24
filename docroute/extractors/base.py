"""Base Extractor Interface for DocRoute."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from docroute.models.extraction import PageExtraction
from docroute.models.profile import PageProfile

class BaseExtractor(ABC):
    """Abstract base class for extraction strategies."""

    @abstractmethod
    def extract_page(
        self, file_path: str, page_number: int, profile: PageProfile
    ) -> PageExtraction:
        """Extracts content from a single page of a document file.
        
        Args:
            file_path: Absolute path to the PDF or image document
            page_number: 1-indexed page number
            profile: Previously generated PageProfile for context
            
        Returns:
            PageExtraction model containing text, tables, and provenance
        """
        pass

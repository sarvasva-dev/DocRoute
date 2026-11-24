"""DocRoute Extractors Package Initialization"""
from docroute.extractors.base import BaseExtractor
from docroute.extractors.native import NativePDFExtractor
from docroute.extractors.ocr import OCRExtractor
from docroute.extractors.tables import TableExtractor
from docroute.extractors.akshar import AksharExtractor
from docroute.extractors.mirage import MirageExtractor

__all__ = [
    "BaseExtractor",
    "NativePDFExtractor",
    "OCRExtractor",
    "TableExtractor",
    "AksharExtractor",
    "MirageExtractor",
]

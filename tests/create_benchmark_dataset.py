"""Benchmark Dataset Generator for DocRoute."""
import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import numpy as np

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data"))

def generate_native_text_pdf(path: str) -> None:
    """Generates a clean native vector text PDF."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    text = (
        "DocRoute Framework Benchmark Report\n\n"
        "1. Executive Summary\n"
        "DocRoute is an adaptive document intelligence engine designed to process "
        "native vector PDFs, scanned documents, and complex layouts seamlessly.\n\n"
        "2. Core Performance Indicators\n"
        "Native extraction operates at high throughput while maintaining exact character fidelity. "
        "When native quality scores fall below threshold, OpenCV preprocessed Tesseract OCR is invoked."
    )
    page.insert_text((50, 70), text, fontsize=12, fontname="helv")
    doc.save(path)
    doc.close()

def generate_scanned_pdf(path: str, text: str = "CONFIDENTIAL FINANCIAL REPORT 2026\nQuarterly Revenue: $4,500,000\nNet Operating Profit: $1,250,000") -> None:
    """Generates a scanned raster image PDF."""
    img = Image.new("RGB", (800, 1000), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Add text to image buffer
    draw.text((60, 80), text, fill=(20, 20, 20))
    # Add noise lines to simulate scan artifacts
    draw.line([(0, 150), (800, 150)], fill=(200, 200, 200), width=1)
    draw.line([(50, 0), (50, 1000)], fill=(220, 220, 220), width=1)

    import io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(0, 0, 595, 842)
    page.insert_image(rect, stream=img_bytes)
    doc.save(path)
    doc.close()

def generate_mixed_pdf(path: str) -> None:
    """Generates a 2-page PDF: Page 1 native text, Page 2 scanned image."""
    doc = fitz.open()
    # Page 1: Native
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 70), "Mixed PDF Document - Page 1 (Native Vector Text Layer)\nClean structured content.", fontsize=12)

    # Page 2: Scanned Image
    img = Image.new("RGB", (800, 1000), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.text((60, 80), "Mixed PDF Document - Page 2 (Scanned Image Content)\nInvoice Number: INV-99823", fill=(10, 10, 10))
    import io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    p2 = doc.new_page(width=595, height=842)
    p2.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_bytes)

    doc.save(path)
    doc.close()

def generate_table_heavy_pdf(path: str) -> None:
    """Generates a PDF containing a structured table with borders."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Title
    page.insert_text((50, 50), "Quarterly Financial Balance Sheet", fontsize=14, fontname="helv")

    # Table grid coordinates
    x0, y0 = 50, 90
    col_widths = [120, 120, 120, 120]
    row_height = 25
    table_data = [
        ["Quarter", "Revenue", "Expense", "Net Income"],
        ["Q1 2026", "$1,200,000", "$800,000", "$400,000"],
        ["Q2 2026", "$1,450,000", "$910,000", "$540,000"],
        ["Q3 2026", "$1,600,000", "$980,000", "$620,000"]
    ]

    for r_idx, row in enumerate(table_data):
        curr_y = y0 + (r_idx * row_height)
        for c_idx, val in enumerate(row):
            curr_x = x0 + sum(col_widths[:c_idx])
            w = col_widths[c_idx]
            rect = fitz.Rect(curr_x, curr_y, curr_x + w, curr_y + row_height)
            page.draw_rect(rect, color=(0, 0, 0), width=0.5)
            font_name = "helv"
            page.insert_text((curr_x + 5, curr_y + 17), val, fontsize=10, fontname=font_name)

    doc.save(path)
    doc.close()

def generate_hindi_doc_pdf(path: str) -> None:
    """Generates a PDF document with Hindi (Devanagari) content."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    hindi_text = "DocRoute दस्तावेज प्रसंस्करण इंजन\nयह एक हिंदी भाषा का परीक्षण दस्तावेज है।\nगुणवत्ता स्कोर और ओसीआर मार्ग का परीक्षण।"
    page.insert_text((50, 70), hindi_text, fontsize=14)
    doc.save(path)
    doc.close()

def build_all_benchmark_files() -> None:
    """Generates all target test files in test_data directory."""
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    generate_native_text_pdf(os.path.join(BENCHMARK_DIR, "native_text.pdf"))
    generate_scanned_pdf(os.path.join(BENCHMARK_DIR, "scanned_page.pdf"))
    generate_mixed_pdf(os.path.join(BENCHMARK_DIR, "mixed_document.pdf"))
    generate_table_heavy_pdf(os.path.join(BENCHMARK_DIR, "table_heavy.pdf"))
    generate_hindi_doc_pdf(os.path.join(BENCHMARK_DIR, "hindi_doc.pdf"))
    generate_scanned_pdf(os.path.join(BENCHMARK_DIR, "poor_quality_scan.pdf"), text="DEGRADED SCAN NOISY TEXT\nAccount: 4892-1102\nAmount Due: $980.50")
    print(f"Generated benchmark dataset in: {BENCHMARK_DIR}")

if __name__ == "__main__":
    build_all_benchmark_files()

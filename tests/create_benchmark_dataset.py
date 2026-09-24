"""Deterministic Benchmark Dataset Generator for DocRoute.

Generates local synthetic benchmark PDFs into tests/_generated/ for testing and benchmarking.
This directory is gitignored to keep the repository lightweight and clean.
"""
import os
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Default local output directory (gitignored)
GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "_generated"))
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))

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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()

def generate_scanned_pdf(path: str, text: str = "CONFIDENTIAL FINANCIAL REPORT 2026\nQuarterly Revenue: $4,500,000\nNet Operating Profit: $1,250,000") -> None:
    """Generates a scanned raster image PDF."""
    img = Image.new("RGB", (800, 1000), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.text((60, 80), text, fill=(20, 20, 20))
    draw.line([(0, 150), (800, 150)], fill=(200, 200, 200), width=1)
    draw.line([(50, 0), (50, 1000)], fill=(220, 220, 220), width=1)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(0, 0, 595, 842)
    page.insert_image(rect, stream=img_bytes)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()

def generate_mixed_pdf(path: str) -> None:
    """Generates a 2-page PDF: Page 1 native text, Page 2 scanned image."""
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 70), "Mixed PDF Document - Page 1 (Native Vector Text Layer)\nClean structured content.", fontsize=12, fontname="helv")

    img = Image.new("RGB", (800, 1000), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.text((60, 80), "Mixed PDF Document - Page 2 (Scanned Image Content)\nInvoice Number: INV-99823", fill=(10, 10, 10))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    p2 = doc.new_page(width=595, height=842)
    p2.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_bytes)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()

def generate_table_heavy_pdf(path: str) -> None:
    """Generates a PDF containing a structured table with borders."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Quarterly Financial Balance Sheet", fontsize=14, fontname="helv")

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
            page.insert_text((curr_x + 5, curr_y + 17), val, fontsize=10, fontname="helv")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()

def generate_hindi_doc_pdf(path: str) -> None:
    """Generates a PDF document with Hindi (Devanagari) content."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    hindi_text = "DocRoute दस्तावेज प्रसंस्करण इंजन\nयह एक हिंदी भाषा का परीक्षण दस्तावेज है।\nगुणवत्ता स्कोर और ओसीआर मार्ग का परीक्षण।"
    page.insert_text((50, 70), hindi_text, fontsize=14)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()

def build_benchmark_dataset(target_dir: str = GENERATED_DIR) -> str:
    """Generates synthetic benchmark test PDFs into local gitignored directory."""
    os.makedirs(target_dir, exist_ok=True)
    generate_native_text_pdf(os.path.join(target_dir, "native_text.pdf"))
    generate_scanned_pdf(os.path.join(target_dir, "scanned_page.pdf"))
    generate_mixed_pdf(os.path.join(target_dir, "mixed_document.pdf"))
    generate_table_heavy_pdf(os.path.join(target_dir, "table_heavy.pdf"))
    generate_hindi_doc_pdf(os.path.join(target_dir, "hindi_doc.pdf"))
    generate_scanned_pdf(
        os.path.join(target_dir, "poor_quality_scan.pdf"),
        text="DEGRADED SCAN NOISY TEXT\nAccount: 4892-1102\nAmount Due: $980.50"
    )
    print(f"Generated benchmark dataset in: {target_dir}")
    return target_dir

def build_minimal_fixtures(target_dir: str = FIXTURES_DIR) -> str:
    """Generates small deterministic fixtures for unit tests."""
    os.makedirs(target_dir, exist_ok=True)
    generate_native_text_pdf(os.path.join(target_dir, "tiny_native.pdf"))
    generate_scanned_pdf(os.path.join(target_dir, "tiny_scan.pdf"))
    generate_table_heavy_pdf(os.path.join(target_dir, "tiny_table.pdf"))
    print(f"Generated minimal fixtures in: {target_dir}")
    return target_dir

if __name__ == "__main__":
    import sys
    if "--fixtures" in sys.argv:
        build_minimal_fixtures()
    else:
        build_benchmark_dataset()

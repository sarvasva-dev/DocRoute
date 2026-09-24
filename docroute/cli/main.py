"""DocRoute Command Line Interface (CLI)."""
import sys
import json
import argparse
import logging
from typing import List

from docroute.core.engine import DocRouteEngine
from docroute.core.profiler import DocumentProfiler
from docroute.models.api import ProcessingOptions

logging.basicConfig(level=logging.WARNING)

def inspect_cmd(args: argparse.Namespace) -> None:
    """CLI inspect command: prints high-level document metadata and layout signals."""
    profiler = DocumentProfiler()
    profile = profiler.profile_document(args.file_path)
    print(f"=== DocRoute Inspection: {profile.document_id} ===")
    print(f"Page Count        : {profile.page_count}")
    print(f"Is Native PDF     : {profile.is_native_pdf}")
    print(f"Is Scanned PDF    : {profile.is_scanned_pdf}")
    print(f"Is Mixed PDF      : {profile.is_mixed_pdf}")
    print(f"Avg Text Density  : {profile.avg_text_density:.2f} chars/kpt²")
    print(f"Primary Language  : {profile.primary_language}")
    print(f"Has Tables        : {profile.is_table_heavy}")
    print("-" * 50)
    for p in profile.pages:
        print(f"Page {p.page_number:2d} | Native Chars: {p.native_char_count:4d} | Density: {p.text_density:5.2f} | Scan Likelihood: {p.scan_likelihood:4.2f}")

def profile_cmd(args: argparse.Namespace) -> None:
    """CLI profile command: prints full DocumentProfile in structured JSON format."""
    profiler = DocumentProfiler()
    profile = profiler.profile_document(args.file_path)
    print(json.dumps(profile.model_dump(), indent=2))

def extract_cmd(args: argparse.Namespace) -> None:
    """CLI extract command: executes adaptive processing pipeline."""
    opts = ProcessingOptions(
        ocr_threshold=args.threshold,
        force_ocr=args.force_ocr,
        language=args.lang,
        extract_tables=not args.no_tables
    )
    engine = DocRouteEngine(options=opts)
    doc = engine.process_document(args.file_path)

    if args.json:
        print(json.dumps(doc.model_dump(), indent=2))
    else:
        print(f"=== Structured Extraction Result: {doc.document_id} ===")
        print(f"Overall Quality Score : {doc.overall_quality.overall_score:.2f}")
        print(f"Route Selected        : {doc.overall_quality.extraction_route}")
        print("=" * 60)
        for page in doc.pages:
            print(f"\n--- PAGE {page.page_number} [{page.extraction_method.upper()}] (Quality: {page.quality.overall_score:.2f}) ---")
            print(page.text)
            if page.tables:
                print(f"\n[Extracted {len(page.tables)} Table(s)]")
                for idx, tab in enumerate(page.tables):
                    print(f"  Table #{idx+1} ({tab.num_rows}x{tab.num_cols}): Headers = {tab.headers}")

def ocr_cmd(args: argparse.Namespace) -> None:
    """CLI ocr command: forces OCR processing on target document."""
    opts = ProcessingOptions(
        force_ocr=True,
        language=args.lang,
        extract_tables=not args.no_tables
    )
    engine = DocRouteEngine(options=opts)
    doc = engine.process_document(args.file_path)

    if args.json:
        print(json.dumps(doc.model_dump(), indent=2))
    else:
        print(f"=== Forced OCR Extraction Result: {doc.document_id} ===")
        for page in doc.pages:
            print(f"\n--- PAGE {page.page_number} [OCR FORCED] (Confidence: {page.quality.ocr_confidence:.1f}%) ---")
            print(page.text)

def main() -> None:
    """Main CLI entrypoint parser."""
    parser = argparse.ArgumentParser(
        prog="docroute",
        description="DocRoute: Adaptive Document Intelligence Engine CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect document layout and scan likelihood")
    p_inspect.add_argument("file_path", help="Path to target PDF or image file")
    p_inspect.set_defaults(func=inspect_cmd)

    # profile
    p_profile = subparsers.add_parser("profile", help="Output document profile as JSON")
    p_profile.add_argument("file_path", help="Path to target PDF or image file")
    p_profile.set_defaults(func=profile_cmd)

    # extract
    p_extract = subparsers.add_parser("extract", help="Adaptively extract document text, tables, and metadata")
    p_extract.add_argument("file_path", help="Path to target PDF or image file")
    p_extract.add_argument("--threshold", type=float, default=0.5, help="OCR quality threshold (default: 0.5)")
    p_extract.add_argument("--force-ocr", action="store_true", help="Force OCR on all pages")
    p_extract.add_argument("--lang", default="eng", help="OCR language (e.g. eng, hin, eng+hin)")
    p_extract.add_argument("--no-tables", action="store_true", help="Disable table extraction")
    p_extract.add_argument("--json", action="store_true", help="Output full structured document as JSON")
    p_extract.set_defaults(func=extract_cmd)

    # ocr
    p_ocr = subparsers.add_parser("ocr", help="Force OCR processing on document")
    p_ocr.add_argument("file_path", help="Path to target PDF or image file")
    p_ocr.add_argument("--lang", default="eng", help="OCR language (e.g. eng, hin, eng+hin)")
    p_ocr.add_argument("--no-tables", action="store_true", help="Disable table extraction")
    p_ocr.add_argument("--json", action="store_true", help="Output full structured document as JSON")
    p_ocr.set_defaults(func=ocr_cmd)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()

"""DocRoute Reproducible Benchmark & Accuracy Evaluation Engine."""
import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from docroute.core.engine import DocRouteEngine
from docroute.models.api import ProcessingOptions

logger = logging.getLogger(__name__)

# Default benchmark dataset directory (gitignored)
DEFAULT_BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "_generated"))
OUTPUT_BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".tmp"))

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def calculate_cer(ground_truth: str, hypothesis: str) -> float:
    """Calculates Character Error Rate (CER) = Edit Distance / len(Ground Truth)."""
    gt_clean = ground_truth.strip()
    hyp_clean = hypothesis.strip()
    if not gt_clean:
        return 0.0 if not hyp_clean else 1.0
    dist = levenshtein_distance(gt_clean, hyp_clean)
    return float(dist) / float(len(gt_clean))

class DocRouteBenchmarkSuite:
    """Executes benchmark evaluation across local dataset and calculates reproducible metrics."""

    def __init__(self, test_data_dir: Optional[str] = None):
        self.test_data_dir = test_data_dir or DEFAULT_BENCHMARK_DIR
        self._ensure_dataset_exists()
        self.engine = DocRouteEngine()

    def _ensure_dataset_exists(self) -> None:
        """Automatically calls generator if local benchmark dataset is missing."""
        if not os.path.exists(self.test_data_dir) or not os.listdir(self.test_data_dir):
            logger.info("Local benchmark dataset missing. Invoking generator...")
            from tests.create_benchmark_dataset import build_benchmark_dataset
            build_benchmark_dataset(self.test_data_dir)

    def run_benchmark(self) -> Dict[str, Any]:
        """Runs benchmark suite over local test dataset files."""
        files = [
            f for f in os.listdir(self.test_data_dir)
            if f.endswith((".pdf", ".png", ".jpg", ".jpeg"))
        ]

        results = []
        total_pages = 0
        native_routes = 0
        ocr_routes = 0
        processing_times: List[float] = []
        cer_scores: List[float] = []

        ground_truths = {
            "native_text.pdf": "DocRoute Framework Benchmark Report Executive Summary Core Performance Indicators",
            "scanned_page.pdf": "CONFIDENTIAL FINANCIAL REPORT 2026 Quarterly Revenue: $4,500,000 Net Operating Profit: $1,250,000",
            "mixed_document.pdf": "Mixed PDF Document Page 1 Invoice Number: INV-99823",
            "table_heavy.pdf": "Quarterly Financial Balance Sheet Q1 2026 Q2 2026 Q3 2026 Revenue Expense Net Income",
            "hindi_doc.pdf": "DocRoute दस्तावेज प्रसंस्करण इंजन"
        }

        for fname in files:
            fpath = os.path.join(self.test_data_dir, fname)
            t0 = time.perf_counter()
            doc = self.engine.process_document(fpath)
            t1 = time.perf_counter()
            proc_time_ms = (t1 - t0) * 1000.0

            file_pages = len(doc.pages)
            total_pages += file_pages
            processing_times.append(proc_time_ms / max(1, file_pages))

            for page in doc.pages:
                if page.extraction_method == "native":
                    native_routes += 1
                else:
                    ocr_routes += 1

            # CER calculation if ground truth is defined
            cer = None
            if fname in ground_truths:
                gt = ground_truths[fname]
                extracted_text = " ".join(p.text for p in doc.pages)
                cer = calculate_cer(gt, extracted_text)
                cer_scores.append(cer)

            results.append({
                "filename": fname,
                "page_count": file_pages,
                "overall_quality": doc.overall_quality.overall_score,
                "route": doc.overall_quality.extraction_route,
                "processing_time_ms": round(proc_time_ms, 2),
                "cer": round(cer, 4) if cer is not None else None,
                "tables_found": sum(len(p.tables) for p in doc.pages)
            })

        avg_page_time = float(np.mean(processing_times)) if processing_times else 0.0
        avg_cer = float(np.mean(cer_scores)) if cer_scores else 0.0

        summary = {
            "dataset_type": "Synthetic/Local Benchmark Suite",
            "total_documents_tested": len(files),
            "total_pages_tested": total_pages,
            "native_route_count": native_routes,
            "ocr_fallback_count": ocr_routes,
            "native_success_rate": round(native_routes / max(1, total_pages), 4),
            "ocr_fallback_rate": round(ocr_routes / max(1, total_pages), 4),
            "avg_page_processing_time_ms": round(avg_page_time, 2),
            "average_cer": round(avg_cer, 4),
            "detailed_results": results
        }

        # Save output to local .tmp directory (gitignored)
        os.makedirs(OUTPUT_BENCHMARK_DIR, exist_ok=True)
        out_json = os.path.join(OUTPUT_BENCHMARK_DIR, "benchmark_results.json")
        with open(out_json, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

if __name__ == "__main__":
    suite = DocRouteBenchmarkSuite()
    report = suite.run_benchmark()
    print(json.dumps(report, indent=2))

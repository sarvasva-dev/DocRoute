"""DocRoute Reproducible Benchmark & Accuracy Evaluation Engine."""
import os
import time
import json
import logging
from typing import Dict, Any, List, Tuple
import numpy as np

from docroute.core.engine import DocRouteEngine
from docroute.models.api import ProcessingOptions

logger = logging.getLogger(__name__)

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

def calculate_wer(ground_truth: str, hypothesis: str) -> float:
    """Calculates Word Error Rate (WER)."""
    gt_words = ground_truth.strip().split()
    hyp_words = hypothesis.strip().split()
    if not gt_words:
        return 0.0 if not hyp_words else 1.0
    dist = levenshtein_distance(" ".join(gt_words), " ".join(hyp_words))
    return float(dist) / float(len(" ".join(gt_words)))

class DocRouteBenchmarkSuite:
    """Executes benchmark evaluation across test dataset and calculates reproducible metrics."""

    def __init__(self, test_data_dir: str):
        self.test_data_dir = test_data_dir
        self.engine = DocRouteEngine()

    def run_benchmark(self) -> Dict[str, Any]:
        """Runs benchmark suite over test dataset files."""
        if not os.path.exists(self.test_data_dir):
            raise FileNotFoundError(f"Test data directory not found: {self.test_data_dir}")

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

        return summary

if __name__ == "__main__":
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "test_data"))
    suite = DocRouteBenchmarkSuite(test_dir)
    report = suite.run_benchmark()
    print(json.dumps(report, indent=2))

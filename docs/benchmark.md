# DocRoute Performance & Quality Benchmark Report

*Note: Benchmark results were measured on the local synthetic test suite using `docroute/benchmark.py` and `tests/create_benchmark_dataset.py`.*

---

## 1. Summary Metrics

| Metric | Measured Value | Description |
| :--- | :--- | :--- |
| **Dataset Corpus** | 6 synthetic test documents (7 pages total) | Includes native vector PDF, noisy scan, table matrix, and Hindi text |
| **Native Route Latency** | ~17.4 ms / page | High-speed vector parsing via PyMuPDF |
| **OCR Pipeline Latency** | ~471.4 ms / page | Includes 200 DPI rendering, OpenCV deskewing & Tesseract OCR |
| **Scanned Page Accuracy** | 92.8% text accuracy | Character Error Rate (CER) = 0.0722 on scanned page |
| **OCR Fallback Rate** | 57.1% | Triggered strictly when native quality score < 0.50 |

---

## 2. Reproducing the Benchmark

To execute the benchmark locally:

```bash
# 1. Generate local synthetic benchmark documents (saved in tests/_generated/)
python tests/create_benchmark_dataset.py

# 2. Run benchmark evaluation
python -m docroute.benchmark
```

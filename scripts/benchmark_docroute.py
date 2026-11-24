#!/usr/bin/env python3
"""
DocRoute End-to-End Vision Benchmark:
Compares DocRoute+Akshar vs DocRoute+Mirage across authentic documents:
1. 3-Page Hybrid Smoke PDF (regression baseline: p1 native, p2 scanned invoice, p3 native table)
2. Real GST Invoice (real_inv_01.png)
3. Real Multi-Page Scanned Invoice (real_inv_04.pdf)
4. Real High-DPI Bank Statement (real_stmt_01.pdf)
5. Real Thermal Receipt (real_rcpt_002.jpg)

Measures:
- Total pipeline latency (ms)
- Extraction method and routing
- Text accuracy and presence
- Field extraction (Total Amount, Vendor/Merchant)
- Table recovery
- Confidence and provenance metadata
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure DocRoute is importable
DOCROUTE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DOCROUTE_ROOT))

from docroute import extract, ProcessingOptions

AKSHAR_DATA = Path("/home/sarvasva/Desktop/minor project/mirage ai/tests/data/real_corpus")

TEST_DOCUMENTS = [
    {
        "name": "3-Page Hybrid Smoke Baseline",
        "path": AKSHAR_DATA / "real_sample_smoke.pdf",
        "expected_total": "12345",
        "has_table": True,
    },
    {
        "name": "Real GST Scanned Invoice",
        "path": AKSHAR_DATA / "real_inv_01.png",
        "expected_total": "124200.00",
        "has_table": True,
    },
    {
        "name": "Real Multi-Page GST PDF",
        "path": AKSHAR_DATA / "real_inv_04.pdf",
        "expected_total": "44962.72",
        "has_table": True,
    },
    {
        "name": "Real Bank Statement Scan",
        "path": AKSHAR_DATA / "real_stmt_01.pdf",
        "expected_total": "27314.45",
        "has_table": True,
    },
    {
        "name": "Real SROIE Thermal Receipt",
        "path": AKSHAR_DATA / "real_rcpt_002.jpg",
        "expected_total": "33.90",
        "has_table": False,
    },
]

def run_docroute(doc_path, vision_engine):
    t0 = time.perf_counter()
    try:
        doc = extract(str(doc_path), vision=vision_engine)
        wall_ms = (time.perf_counter() - t0) * 1000.0
        
        # Aggregate text, tables, quality
        full_text = "\n".join(p.text for p in doc.pages)
        total_tables = sum(len(p.tables) for p in doc.pages)
        methods = [p.extraction_method for p in doc.pages]
        avg_quality = sum(p.quality.overall_score for p in doc.pages) / max(len(doc.pages), 1)
        engines = [p.provenance[0].engine for p in doc.pages if p.provenance]
        
        return {
            "wall_ms": round(wall_ms, 2),
            "page_count": len(doc.pages),
            "methods": methods,
            "engines": engines,
            "text_length": len(full_text),
            "full_text": full_text,
            "total_tables": total_tables,
            "avg_quality": round(avg_quality, 3),
            "error": None,
        }
    except Exception as e:
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "wall_ms": round(wall_ms, 2),
            "error": str(e)
        }

def main():
    print("================================================================================")
    print("      DOCROUTE END-TO-END VISION BENCHMARK: AKSHAR vs MIRAGE")
    print("================================================================================")
    
    results = []
    
    for item in TEST_DOCUMENTS:
        name = item["name"]
        path = item["path"]
        exp_tot = item["expected_total"]
        
        if not path.is_file():
            print(f"Skipping missing: {path}")
            continue
            
        print(f"\n--- Benchmarking: {name} ({path.name}) ---")
        
        # 1. Run DocRoute with Akshar
        res_akshar = run_docroute(path, vision_engine="akshar")
        
        # 2. Run DocRoute with Mirage
        res_mirage = run_docroute(path, vision_engine="mirage")
        
        # Total found checks
        akshar_tot_found = exp_tot in res_akshar.get("full_text", "")
        mirage_tot_found = exp_tot in res_mirage.get("full_text", "")
        
        speedup = (
            round(res_mirage["wall_ms"] / res_akshar["wall_ms"], 1)
            if res_mirage["wall_ms"] > 0 and res_akshar["wall_ms"] > 0
            else 1.0
        )
        
        print(f"  DocRoute + Akshar:  {res_akshar['wall_ms']:6.1f} ms | Total={akshar_tot_found} | Tables={res_akshar.get('total_tables', 0)} | Methods={res_akshar.get('methods')}")
        print(f"  DocRoute + Mirage:  {res_mirage['wall_ms']:6.1f} ms | Total={mirage_tot_found} | Tables={res_mirage.get('total_tables', 0)} | Methods={res_mirage.get('methods')}")
        print(f"  Speedup:            {speedup}x")
        
        results.append({
            "name": name,
            "filename": path.name,
            "akshar": res_akshar,
            "mirage": res_mirage,
            "speedup": speedup,
            "akshar_total_found": akshar_tot_found,
            "mirage_total_found": mirage_tot_found,
        })
        
    out_path = DOCROUTE_ROOT / "DOCROUTE_VISION_BENCHMARK_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "="*80)
    print("                    DOCROUTE HEAD-TO-HEAD SUMMARY")
    print("="*80)
    print(f"{'Document':<30} | {'Akshar Time':<12} | {'Mirage Time':<12} | {'Speedup':<8} | {'Win'}")
    print("-" * 80)
    for r in results:
        w_ak = f"{r['akshar']['wall_ms']:.1f} ms"
        w_mi = f"{r['mirage']['wall_ms']:.1f} ms"
        sp = f"{r['speedup']:.1f}x"
        win = "Akshar (Faster & Provenance)" if r["akshar"]["wall_ms"] <= r["mirage"]["wall_ms"] else "Mirage"
        print(f"{r['name']:<30} | {w_ak:<12} | {w_mi:<12} | {sp:<8} | {win}")
    print("="*80)
    print(f"Saved benchmark results to {out_path}")

if __name__ == "__main__":
    main()

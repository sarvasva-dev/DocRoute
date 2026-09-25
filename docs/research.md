# Document Intelligence & Extraction Best Practices Research

This document summarizes technical research on current document extraction methodologies.

---

## 1. Vector PDF Extraction (PyMuPDF / fitz)
- Direct vector stream parsing retrieves character positions and font metrics without rasterization overhead.
- Native extraction achieves ~15-20ms per page throughput.

## 2. Computer Vision Preprocessing (OpenCV)
- **Binarization**: Otsu thresholding provides optimal separation for uneven lighting.
- **Deskewing**: MinAreaRect contour analysis detects rotation angles (-45° to +45°) to align text horizontally prior to OCR.

## 3. Tesseract OCR Engine (v5.4)
- LSTM neural network line recognizer.
- Multi-language engine support (`eng`, `hin`).
- Provides word-level confidence and bounding polygon data.

## 4. Adaptive Quality Fallback Routing
- Objective quality evaluation evaluates garbage character ratios, printable ASCII density, and dictionary word match ratios to decide between vector native and OCR fallback.

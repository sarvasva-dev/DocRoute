"""FastAPI API Routes for DocRoute Engine (Versioned /v1 Namespace)."""
import os
import re
import uuid
import tempfile
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse

from docroute.models.document import StructuredDocument
from docroute.models.profile import DocumentProfile
from docroute.models.extraction import PageExtraction
from docroute.models.table import TableData
from docroute.models.quality import QualityScore
from docroute.models.api import ProcessingOptions, ErrorResponse
from docroute.core.engine import DocRouteEngine
from docroute.core.profiler import DocumentProfiler

logger = logging.getLogger(__name__)

# Primary V1 API Router
v1_router = APIRouter(prefix="/v1", tags=["V1 API"])

# In-memory document storage cache for active session requests
DOCUMENT_STORE: Dict[str, StructuredDocument] = {}
PROFILE_STORE: Dict[str, DocumentProfile] = {}
FILE_PATH_STORE: Dict[str, str] = {}

MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

def _validate_path_security(filename: str) -> str:
    """Prevents directory traversal security vulnerabilities."""
    clean_name = os.path.basename(filename)
    if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FILENAME",
                    "message": "Potential path traversal detected in filename."
                }
            }
        )
    return clean_name

@v1_router.get("", tags=["Discovery"])
async def v1_api_discovery():
    """V1 API metadata discovery endpoint."""
    return {
        "api_version": "v1",
        "service": "docroute-api",
        "endpoints": [
            "POST /v1/ocr",
            "POST /v1/documents",
            "GET /v1/documents/{document_id}",
            "GET /v1/documents/{document_id}/pages",
            "GET /v1/documents/{document_id}/text",
            "GET /v1/documents/{document_id}/tables",
            "GET /v1/documents/{document_id}/quality",
            "GET /v1/documents/{document_id}/vision",
            "GET /v1/documents/{document_id}/kv-pairs"
        ]
    }

@v1_router.post("/ocr", status_code=status.HTTP_200_OK)
async def process_ocr_unified(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("eng"),
    engine_name: str = Form("auto"),
    extract_tables: bool = Form(True),
    include_provenance: bool = Form(True),
    quality_threshold: float = Form(0.5),
    max_pages: int = Form(50)
):
    """Primary unified OCR & document extraction endpoint."""
    clean_filename = _validate_path_security(file.filename)
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": f"File extension '{ext}' is not supported. Use PDF, PNG, JPG, JPEG, TIFF, WEBP."
                }
            }
        )

    # Save to temp file securely
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix="docroute_ocr_")
    saved_path = temp_file.name

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "EMPTY_FILE",
                        "message": "Uploaded file is empty (0 bytes)."
                    }
                }
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
                    }
                }
            )

        temp_file.write(content)
        temp_file.close()

        opts = ProcessingOptions(
            ocr_threshold=quality_threshold,
            force_ocr=(engine_name.lower() == "tesseract"),
            language=language,
            extract_tables=extract_tables,
            max_pages=max_pages
        )

        doc_engine = DocRouteEngine(options=opts)
        structured_doc = doc_engine.process_document(saved_path, options_override=opts)
        doc_profile = doc_engine.profiler.profile_document(saved_path, max_pages=max_pages)

        doc_id = structured_doc.document_id
        DOCUMENT_STORE[doc_id] = structured_doc
        PROFILE_STORE[doc_id] = doc_profile
        FILE_PATH_STORE[doc_id] = saved_path

        full_text = "\n\n".join(p.text for p in structured_doc.pages)
        all_tables = []
        all_provenance = []
        for p in structured_doc.pages:
            all_tables.extend(p.tables)
            if include_provenance:
                all_provenance.extend(p.provenance)

        engines_used = list(set(rec.engine for rec in all_provenance if hasattr(rec, 'engine')))
        if not engines_used:
            engines_used = ["pymupdf-native"]

        return {
            "request_id": getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}"),
            "document_id": doc_id,
            "status": "completed",
            "filename": clean_filename,
            "total_pages": len(structured_doc.pages),
            "pages": [p.dict() for p in structured_doc.pages],
            "text": full_text,
            "tables": [t.dict() for t in all_tables],
            "extraction": {
                "route": structured_doc.pages[0].extraction_method if structured_doc.pages else "native",
                "engines": engines_used
            },
            "quality": structured_doc.overall_quality.dict(),
            "provenance": [pr.dict() for pr in all_provenance] if include_provenance else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed for uploaded file {clean_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "PROCESSING_FAILURE",
                    "message": f"Document extraction failed: {str(e)}"
                }
            }
        )

@v1_router.post("/documents", response_model=StructuredDocument, status_code=status.HTTP_201_CREATED)
async def upload_and_process_document_v1(
    file: UploadFile = File(...),
    ocr_threshold: float = Query(0.5, ge=0.0, le=1.0),
    force_ocr: bool = Query(False),
    language: str = Query("eng"),
    extract_tables: bool = Query(True),
    max_pages: int = Query(50, ge=1, le=500)
):
    """Uploads a PDF or image file and returns full structured document model."""
    clean_filename = _validate_path_security(file.filename)
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": f"Unsupported format '{ext}'."
                }
            }
        )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix="docroute_doc_")
    saved_path = temp_file.name

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "EMPTY_FILE", "message": "Uploaded file is empty."}}
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"error": {"code": "FILE_TOO_LARGE", "message": "File exceeds size limit."}}
            )

        temp_file.write(content)
        temp_file.close()

        opts = ProcessingOptions(
            ocr_threshold=ocr_threshold,
            force_ocr=force_ocr,
            language=language,
            extract_tables=extract_tables,
            max_pages=max_pages
        )

        doc_engine = DocRouteEngine(options=opts)
        structured_doc = doc_engine.process_document(saved_path, options_override=opts)
        doc_profile = doc_engine.profiler.profile_document(saved_path, max_pages=max_pages)

        doc_id = structured_doc.document_id
        DOCUMENT_STORE[doc_id] = structured_doc
        PROFILE_STORE[doc_id] = doc_profile
        FILE_PATH_STORE[doc_id] = saved_path

        return structured_doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed for uploaded file {clean_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "PROCESSING_FAILURE", "message": str(e)}}
        )

@v1_router.get("/documents/{document_id}", response_model=StructuredDocument)
async def get_structured_document_v1(document_id: str):
    """Retrieves full structured document extraction payload by ID."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    return DOCUMENT_STORE[document_id]

@v1_router.get("/documents/{document_id}/profile", response_model=DocumentProfile)
async def get_document_profile_v1(document_id: str):
    """Retrieves layout and scan profile for document by ID."""
    if document_id not in PROFILE_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Profile for '{document_id}' not found."}}
        )
    return PROFILE_STORE[document_id]

@v1_router.get("/documents/{document_id}/pages", response_model=List[PageExtraction])
async def get_document_pages_v1(document_id: str):
    """Retrieves list of extracted page models for document by ID."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    return DOCUMENT_STORE[document_id].pages

@v1_router.get("/documents/{document_id}/text", response_model=Dict[str, str])
async def get_document_plain_text_v1(document_id: str):
    """Retrieves plain aggregated text across all document pages."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    doc = DOCUMENT_STORE[document_id]
    aggregated = "\n\n--- Page Break ---\n\n".join(p.text for p in doc.pages)
    return {"document_id": document_id, "text": aggregated}

@v1_router.get("/documents/{document_id}/tables", response_model=List[TableData])
async def get_document_tables_v1(document_id: str):
    """Retrieves all extracted structured tables across document pages."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    doc = DOCUMENT_STORE[document_id]
    all_tables = []
    for page in doc.pages:
        all_tables.extend(page.tables)
    return all_tables

@v1_router.get("/documents/{document_id}/quality", response_model=QualityScore)
async def get_document_quality_v1(document_id: str):
    """Retrieves document overall extraction quality report."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    return DOCUMENT_STORE[document_id].overall_quality

@v1_router.get("/documents/{document_id}/vision")
async def get_google_vision_compatible_schema_v1(document_id: str):
    """Returns Google Cloud Vision API (AnnotateImageResponse) compatible JSON payload."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    doc = DOCUMENT_STORE[document_id]
    return _convert_to_vision_ai_schema(doc)

@v1_router.get("/documents/{document_id}/kv-pairs")
async def get_document_key_value_pairs_v1(document_id: str):
    """Extracts Form Field Key-Value pairs (AWS Textract / Form Recognizer style) from document."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document ID '{document_id}' not found."}}
        )
    doc = DOCUMENT_STORE[document_id]
    return _extract_key_value_pairs(doc)

@v1_router.get("/documents/{document_id}/debug/{page_num}")
async def get_visual_debug_page_v1(document_id: str, page_num: int):
    """Generates visual debug page annotation image showing bounding boxes and route reasoning."""
    if document_id not in FILE_PATH_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Document file for ID '{document_id}' not found."}}
        )
    
    file_path = FILE_PATH_STORE[document_id]
    engine = DocRouteEngine()
    temp_img_path = os.path.join(tempfile.gettempdir(), f"debug_{document_id}_p{page_num}.png")

    try:
        debug_meta = engine.generate_visual_debug_page(file_path, page_num, temp_img_path)
        return FileResponse(temp_img_path, media_type="image/png", filename=f"debug_p{page_num}.png")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DEBUG_IMAGE_ERROR", "message": str(e)}}
        )

# Helper functions for Vision API conversion and Key-Value extraction
def _convert_to_vision_ai_schema(doc: StructuredDocument) -> Dict[str, Any]:
    """Converts DocRoute StructuredDocument payload to Google Cloud Vision AnnotateImageResponse format."""
    responses = []
    for page in doc.pages:
        text_annotations = []
        text_annotations.append({
            "description": page.text,
            "boundingPoly": {
                "vertices": [
                    {"x": 0, "y": 0},
                    {"x": int(page.width), "y": 0},
                    {"x": int(page.width), "y": int(page.height)},
                    {"x": 0, "y": int(page.height)}
                ]
            }
        })
        
        vision_blocks = []
        if page.provenance:
            for rec in page.provenance:
                bbox = rec.bbox or [0, 0, page.width, page.height]
                x0, y0, x1, y1 = [int(v) for v in bbox]
                text_annotations.append({
                    "description": rec.text_snippet,
                    "boundingPoly": {
                        "vertices": [
                            {"x": x0, "y": y0},
                            {"x": x1, "y": y0},
                            {"x": x1, "y": y1},
                            {"x": x0, "y": y1}
                        ]
                    }
                })
                vision_blocks.append({
                    "blockType": "TEXT",
                    "text": rec.text_snippet,
                    "confidence": rec.confidence,
                    "source": rec.engine,
                    "boundingPoly": {
                        "vertices": [
                            {"x": x0, "y": y0},
                            {"x": x1, "y": y0},
                            {"x": x1, "y": y1},
                            {"x": x0, "y": y1}
                        ]
                    }
                })
                
        responses.append({
            "pageNumber": page.page_number,
            "textAnnotations": text_annotations,
            "fullTextAnnotation": {
                "text": page.text,
                "pages": [
                    {
                        "width": int(page.width),
                        "height": int(page.height),
                        "blocks": vision_blocks
                    }
                ]
            }
        })
    return {"responses": responses}

def _extract_key_value_pairs(doc: StructuredDocument) -> List[Dict[str, Any]]:
    """Extracts Form Field Key-Value pairs using spatial layout and delimiter regex heuristics."""
    kv_pairs = []
    kv_pattern = re.compile(r"^([A-Za-z0-9\s_\-\.#]+)\s*[:=]\s*(.+)$")
    
    for page in doc.pages:
        if page.provenance:
            for rec in page.provenance:
                txt = rec.text_snippet.strip()
                match = kv_pattern.match(txt)
                if match:
                    key_part = match.group(1).strip()
                    val_part = match.group(2).strip()
                    if len(key_part) > 1 and len(val_part) > 0 and len(key_part) < 40:
                        kv_pairs.append({
                            "page": page.page_number,
                            "key": key_part,
                            "value": val_part,
                            "confidence": rec.confidence,
                            "bbox": rec.bbox,
                            "source": rec.engine
                        })
    return kv_pairs

# Backward Compatibility Router for /documents (unversioned)
router = APIRouter(prefix="/documents", tags=["Documents (Legacy)"])
router.post("", response_model=StructuredDocument, status_code=status.HTTP_201_CREATED)(upload_and_process_document_v1)
router.get("/{document_id}", response_model=StructuredDocument)(get_structured_document_v1)
router.get("/{document_id}/profile", response_model=DocumentProfile)(get_document_profile_v1)
router.get("/{document_id}/pages", response_model=List[PageExtraction])(get_document_pages_v1)
router.get("/{document_id}/text", response_model=Dict[str, str])(get_document_plain_text_v1)
router.get("/{document_id}/tables", response_model=List[TableData])(get_document_tables_v1)
router.get("/{document_id}/quality", response_model=QualityScore)(get_document_quality_v1)
router.get("/{document_id}/vision")(get_google_vision_compatible_schema_v1)
router.get("/{document_id}/kv-pairs")(get_document_key_value_pairs_v1)
router.get("/{document_id}/debug/{page_num}")(get_visual_debug_page_v1)

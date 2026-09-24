"""FastAPI API Routes for DocRoute Engine."""
import os
import shutil
import tempfile
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status
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

router = APIRouter(prefix="/documents", tags=["Documents"])

# In-memory document storage cache for API requests
DOCUMENT_STORE: Dict[str, StructuredDocument] = {}
PROFILE_STORE: Dict[str, DocumentProfile] = {}
FILE_PATH_STORE: Dict[str, str] = {}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit for security

def _validate_path_security(filename: str) -> str:
    """Prevents directory traversal security vulnerabilities."""
    clean_name = os.path.basename(filename)
    if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: potential path traversal detected."
        )
    return clean_name

@router.post("", response_model=StructuredDocument, status_code=status.HTTP_201_CREATED)
async def upload_and_process_document(
    file: UploadFile = File(...),
    ocr_threshold: float = Query(0.5, ge=0.0, le=1.0),
    force_ocr: bool = Query(False),
    language: str = Query("eng"),
    extract_tables: bool = Query(True)
):
    """Uploads a PDF or image file and returns full structured document intelligence."""
    clean_filename = _validate_path_security(file.filename)
    
    # Verify file extension
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Must be PDF or image."
        )

    # Save to temp directory safely
    temp_dir = tempfile.mkdtemp(prefix="docroute_upload_")
    saved_path = os.path.join(temp_dir, clean_filename)

    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed limit (50MB)."
            )

        with open(saved_path, "wb") as f:
            f.write(content)

        opts = ProcessingOptions(
            ocr_threshold=ocr_threshold,
            force_ocr=force_ocr,
            language=language,
            extract_tables=extract_tables
        )

        engine = DocRouteEngine(options=opts)
        structured_doc = engine.process_document(saved_path, options_override=opts)
        doc_profile = engine.profiler.profile_document(saved_path)

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
            detail=f"Document processing failed: {str(e)}"
        )

@router.get("/{document_id}", response_model=StructuredDocument)
async def get_structured_document(document_id: str):
    """Retrieves full structured document extraction payload by ID."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    return DOCUMENT_STORE[document_id]

@router.get("/{document_id}/profile", response_model=DocumentProfile)
async def get_document_profile(document_id: str):
    """Retrieves layout and scan profile for document by ID."""
    if document_id not in PROFILE_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document profile for ID '{document_id}' not found."
        )
    return PROFILE_STORE[document_id]

@router.get("/{document_id}/pages", response_model=List[PageExtraction])
async def get_document_pages(document_id: str):
    """Retrieves list of extracted page models for document by ID."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    return DOCUMENT_STORE[document_id].pages

@router.get("/{document_id}/text", response_model=Dict[str, str])
async def get_document_plain_text(document_id: str):
    """Retrieves plain aggregated text across all document pages."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    doc = DOCUMENT_STORE[document_id]
    aggregated = "\n\n--- Page Break ---\n\n".join(p.text for p in doc.pages)
    return {"document_id": document_id, "text": aggregated}

@router.get("/{document_id}/tables", response_model=List[TableData])
async def get_document_tables(document_id: str):
    """Retrieves all extracted structured tables across document pages."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    doc = DOCUMENT_STORE[document_id]
    all_tables = []
    for page in doc.pages:
        all_tables.extend(page.tables)
    return all_tables

@router.get("/{document_id}/quality", response_model=QualityScore)
async def get_document_quality(document_id: str):
    """Retrieves document overall extraction quality report."""
    if document_id not in DOCUMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    return DOCUMENT_STORE[document_id].overall_quality

@router.get("/{document_id}/debug/{page_num}")
async def get_visual_debug_page(document_id: str, page_num: int):
    """Generates visual debug page annotation image showing bounding boxes and route reasoning."""
    if document_id not in FILE_PATH_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file for ID '{document_id}' not found."
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
            detail=f"Failed to generate visual debug page: {e}"
        )

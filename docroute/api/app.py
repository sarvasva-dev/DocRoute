"""FastAPI Application Entrypoint for DocRoute API."""
import os
import time
import uuid
import shutil
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse

from docroute.api.routes import v1_router, router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("docroute.api")

app = FastAPI(
    title="DocRoute: Adaptive Document Intelligence API",
    description=(
        "Developer-friendly document extraction API combining native PDF extraction, "
        "OpenCV preprocessing, Tesseract OCR, table parsing, quality-based routing, and spatial provenance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
cors_origins_raw = os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_ORIGIN") or "*"
cors_origins = [o.strip() for o in cors_origins_raw.split(",")] if cors_origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for Request ID & Optional API Key Authentication
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    request.state.request_id = request_id
    
    # Public endpoints that bypass authentication
    public_paths = ["/health", "/ready", "/", "/docs", "/redoc", "/openapi.json"]
    path = request.url.path
    
    # Check optional API Key authentication if DOCROUTE_API_KEY is configured
    api_key_env = os.getenv("DOCROUTE_API_KEY")
    if api_key_env and not any(path.startswith(p) for p in public_paths) and not path.startswith("/dashboard"):
        auth_header = request.headers.get("Authorization", "")
        x_api_key = request.headers.get("X-API-Key", "")
        
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif x_api_key:
            token = x_api_key.strip()
            
        if token != api_key_env:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or missing API key."
                    },
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Include Versioned and Legacy Routers
app.include_router(v1_router)
app.include_router(router)

# Mount Web Dashboard Static Files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/dashboard", StaticFiles(directory=STATIC_DIR, html=True), name="dashboard")

@app.get("/health", tags=["Health"])
async def health_check():
    """Lightweight, public health endpoint for Render health checks and external uptime monitors.
    
    Executes in sub-milliseconds without performing OCR, opening files, or database operations.
    """
    return {
        "status": "ok",
        "service": "docroute-api",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness endpoint verifying core application and OCR binary availability."""
    tesseract_cmd = os.getenv("TESSERACT_CMD") or shutil.which("tesseract") or "tesseract"
    tesseract_available = shutil.which(tesseract_cmd) is not None or os.path.exists(tesseract_cmd)
    
    if not tesseract_available:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "ocr": {"tesseract": "unavailable", "reason": f"Executable '{tesseract_cmd}' not found on PATH."}
            }
        )
        
    return {
        "status": "ready",
        "ocr": {
            "tesseract": "available"
        }
    }

@app.get("/", tags=["UI"])
async def root_entrypoint(request: Request):
    """Root endpoint: Serves interactive Web UI directly or returns API metadata."""
    accept_header = request.headers.get("accept", "")
    index_path = os.path.join(STATIC_DIR, "index.html")
    if "text/html" in accept_header and os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "docroute-api",
        "tagline": "Adaptive Document Intelligence API",
        "status": "ok",
        "version": "1.0.0",
        "dashboard": "/dashboard/",
        "documentation": "/docs",
        "health_check": "/health",
        "readiness_check": "/ready"
    }

@app.get("/style.css", include_in_schema=False)
async def serve_style():
    style_path = os.path.join(STATIC_DIR, "style.css")
    if os.path.exists(style_path):
        return FileResponse(style_path, media_type="text/css")
    return Response(status_code=404)

@app.get("/app.js", include_in_schema=False)
async def serve_js():
    js_path = os.path.join(STATIC_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return Response(status_code=404)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("docroute.api.app:app", host="0.0.0.0", port=port, reload=True)

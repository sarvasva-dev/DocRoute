"""FastAPI Application Entrypoint for DocRoute."""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse

from docroute.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="DocRoute: Adaptive Document Intelligence Engine",
    description=(
        "Production-grade reusable document processing framework combining PyMuPDF native extraction, "
        "OpenCV preprocessing, Tesseract OCR, adaptive quality routing, table parsing, and provenance tracking."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for integration flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount Web Dashboard Static Files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/dashboard", StaticFiles(directory=STATIC_DIR, html=True), name="dashboard")

@app.get("/", tags=["Health"])
async def root_entrypoint(request: Request):
    """Root endpoint: Redirects browser requests to interactive dashboard or returns JSON health."""
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and os.path.exists(STATIC_DIR):
        return RedirectResponse(url="/dashboard/")
    return {
        "service": "DocRoute Engine",
        "status": "online",
        "version": "1.0.0",
        "dashboard": "/dashboard/",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("docroute.api.app:app", host="0.0.0.0", port=8000, reload=True)


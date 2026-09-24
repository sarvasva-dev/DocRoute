"""FastAPI Application Entrypoint for DocRoute."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/", tags=["Health"])
async def root_health_check():
    """Service health check endpoint."""
    return {
        "service": "DocRoute Engine",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("docroute.api.app:app", host="0.0.0.0", port=8000, reload=True)

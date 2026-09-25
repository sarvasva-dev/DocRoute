# Production Dockerfile for DocRoute Adaptive Document Intelligence Engine
FROM python:3.10-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies & Tesseract OCR engine (English + Hindi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Install docroute package in editable/production mode
RUN pip install --no-cache-dir -e .

# Expose default port
EXPOSE 8000

# Default environment variables
ENV PORT=8000
ENV TESSERACT_CMD=/usr/bin/tesseract

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Start FastAPI server via Uvicorn
CMD ["sh", "-c", "uvicorn docroute.api.app:app --host 0.0.0.0 --port ${PORT}"]

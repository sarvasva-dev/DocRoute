# Render Cloud Deployment & Uptime Monitoring Guide

This guide details how to deploy **DocRoute Engine** to Render.com using containerized Docker services, configure native health checks, and set up external uptime monitoring to reduce idle spin-downs on the Render Free tier.

---

## 1. Architecture Overview

```
                      USER BROWSER
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    DocRoute Static UI            DocRoute API
  (Render Static Site)         (Render Web Service)
                                         │
                                         ▼
                                     /v1/ocr

   -----------------------------------------------------

                  EXTERNAL MONITOR (UptimeRobot)
                           │
              (HTTP GET /health every 5 mins)
                           │
                           ▼
                      DocRoute API
                     GET /health (200 OK)
```

---

## 2. Backend Web Service Deployment (Render)

### Docker Environment Configuration
1. In the Render Dashboard, create a **New Web Service**.
2. Connect your GitHub repository: `https://github.com/sarvasva-dev/DocRoute`.
3. Configure settings:
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Region**: Oregon (or nearest region)
   - **Plan**: Free

### Environment Variables
Set the following environment variables in Render:

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port provided by Render (FastAPI binds to `0.0.0.0:$PORT`) |
| `TESSERACT_CMD` | `/usr/bin/tesseract` | System path to Tesseract OCR binary inside Linux container |
| `ENVIRONMENT` | `production` | Deployment environment flag |
| `CORS_ORIGINS` | `*` (or frontend domain) | Allowed origin origins for frontend client |
| `DOCROUTE_API_KEY` | *(Optional)* | Set if API key authentication is required for `/v1/*` endpoints |

### Native Render Health Check Path
Under **Advanced Settings** in Render:
- **Health Check Path**: `/health`

Render natively pings `/health` during deployments to verify that the container is ready before switching traffic.

---

## 3. External Free-Tier Uptime Monitoring (UptimeRobot)

Render Free web services spin down after 15 minutes without inbound HTTP traffic. Because internal Python loops inside a sleeping instance cannot keep it awake, an **EXTERNAL HTTP monitor** is required.

### UptimeRobot Setup Instructions:
1. Register a free account at [UptimeRobot.com](https://uptimerobot.com/).
2. Click **Add New Monitor**.
3. Configure the monitor:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `DocRoute API Health`
   - **URL (or IP)**: `https://YOUR-DOCROUTE-BACKEND.onrender.com/health`
   - **Monitoring Interval**: `5 minutes`
   - **HTTP Status Code**: `200`
4. Click **Create Monitor**.

*Note: External health monitoring is configured to reduce idle spin-downs on the Render Free service. Free Render web services remain subject to platform limits and platform restarts.*

---

## 4. Optional GitHub Actions Fallback Monitor

As an alternative or secondary backup to UptimeRobot, DocRoute includes a scheduled GitHub Action workflow in `.github/workflows/health-check.yml`:

```yaml
name: DocRoute Health Monitor

on:
  schedule:
    - cron: '*/5 * * * *'  # Runs every 5 minutes
  workflow_dispatch:

jobs:
  ping-health:
    runs-on: ubuntu-latest
    steps:
      - name: Ping DocRoute Health Endpoint
        run: |
          curl -f -s https://YOUR-DOCROUTE-BACKEND.onrender.com/health || echo "Endpoint waking up"
```

---

## 5. Lightweight `/health` Endpoint Guarantees

The `/health` endpoint is engineered specifically for uptime monitoring:
- **Authentication**: Publicly accessible without API keys.
- **Execution Latency**: Sub-millisecond response.
- **Resource Usage**: Performs NO OCR, opens NO PDF files, and executes NO heavy database operations.
- **Response Schema**:
  ```json
  {
    "status": "ok",
    "service": "docroute-api",
    "version": "1.0.0",
    "timestamp": "2026-09-25T09:00:00Z",
    "environment": "production"
  }
  ```

---

## 6. Cold-Start Handling in Client Applications

When a free Render web service is spinning up from an idle state, requests may encounter a 502/503/504 gateway response or timeout during the first 10-20 seconds.

The DocRoute Web UI gracefully detects cold starts and displays:
> *"DocRoute API is waking up. Please retry in a moment."*

with a `[Retry]` button and limited exponential backoff (no infinite loops or fake OCR results).

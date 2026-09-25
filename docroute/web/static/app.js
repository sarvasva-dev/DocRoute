/**
 * DocRoute - Adaptive Document Intelligence API Dashboard JS Client
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- State Variables ---
    let selectedFile = null;
    let currentDocument = null; // StructuredDocument or /v1/ocr payload
    let currentProfile = null;  // DocumentProfile payload
    let currentPageIndex = 0;   // 0-indexed
    let activeApiEndpoint = "ocr";
    let activeApiLang = "curl";
    let retryCount = 0;

    // --- DOM Elements ---
    const navBtns = document.querySelectorAll(".nav-btn");
    const viewSections = document.querySelectorAll(".view-section");
    const brandHome = document.getElementById("brand-home");

    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const fileBanner = document.getElementById("file-banner");
    const selectedFileName = document.getElementById("selected-file-name");
    const selectedFileSize = document.getElementById("selected-file-size");
    const btnClearFile = document.getElementById("btn-clear-file");

    const thresholdSlider = document.getElementById("ocr-threshold-slider");
    const thresholdVal = document.getElementById("ocr-threshold-val");
    const ocrLanguageSelect = document.getElementById("ocr-language-select");
    const maxPagesSelect = document.getElementById("max-pages-select");
    const forceOcrToggle = document.getElementById("force-ocr-toggle");
    const extractTablesToggle = document.getElementById("extract-tables-toggle");

    const progressStageBar = document.getElementById("progress-stage-bar");
    const stageLabel = document.getElementById("stage-label");
    const stageProgressFill = document.getElementById("stage-progress-fill");

    const coldStartBanner = document.getElementById("cold-start-banner");
    const btnRetryUpload = document.getElementById("btn-retry-upload");

    const btnProcess = document.getElementById("btn-process");
    const btnProcessText = document.getElementById("btn-process-text");
    const processSpinner = document.getElementById("process-spinner");

    const workspaceResults = document.getElementById("workspace-results");
    
    // Status Badge
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");

    // Dashboard Telemetry DOM
    const dashApiStatus = document.getElementById("dash-api-status");
    const dashLatency = document.getElementById("dash-latency");
    const dashOcrStatus = document.getElementById("dash-ocr-status");
    const dashVersion = document.getElementById("dash-version");

    // Health View DOM
    const healthStatusVal = document.getElementById("health-status-val");
    const readyStatusVal = document.getElementById("ready-status-val");
    const healthTimeVal = document.getElementById("health-time-val");
    const btnRefreshHealth = document.getElementById("btn-refresh-health");

    // Meta Card
    const metaDocId = document.getElementById("meta-doc-id");
    const metaFilename = document.getElementById("meta-filename");
    const metaTotalPages = document.getElementById("meta-total-pages");
    const metaQualityBadge = document.getElementById("meta-quality-badge");

    const gaugeScanPercent = document.getElementById("gauge-scan-percent");
    const gaugeScanFill = document.getElementById("gauge-scan-fill");
    const gaugeScanRec = document.getElementById("gauge-scan-recommendation");

    const btnPrevPage = document.getElementById("btn-prev-page");
    const btnNextPage = document.getElementById("btn-next-page");
    const pageIndicator = document.getElementById("page-indicator");
    const pageRouteBadge = document.getElementById("page-route-badge");

    // Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // Canvas
    const pageCanvas = document.getElementById("page-canvas");
    const bboxTooltip = document.getElementById("bbox-tooltip");

    // Text & Tables
    const extractedTextView = document.getElementById("extracted-text-view");
    const statChars = document.getElementById("stat-chars");
    const statWords = document.getElementById("stat-words");
    const btnCopyText = document.getElementById("btn-copy-text");

    const tableCountBadge = document.getElementById("table-count-badge");
    const tableSelectDropdown = document.getElementById("table-select-dropdown");
    const tableMatrixContainer = document.getElementById("table-matrix-container");
    const btnCopyTableCsv = document.getElementById("btn-copy-table-csv");

    // Pages & Quality & Provenance
    const pagesListContainer = document.getElementById("pages-list-container");
    const qOverall = document.getElementById("q-overall");
    const qOcrConf = document.getElementById("q-ocr-conf");
    const qGarbage = document.getElementById("q-garbage");
    const provenanceTableBody = document.querySelector("#provenance-table tbody");
    const fullJsonView = document.getElementById("full-json-view");
    const btnCopyJson = document.getElementById("btn-copy-json");

    // Playground
    const apiEpItems = document.querySelectorAll(".api-ep-item");
    const langTabs = document.querySelectorAll(".lang-tab");
    const apiCodeContent = document.getElementById("api-code-content");
    const btnCopyCode = document.getElementById("btn-copy-code");

    // --- Toast Notifications ---
    function showToast(msg, duration = 3000) {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = msg;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    }

    // --- View Switcher Router ---
    function switchView(viewId) {
        viewSections.forEach(sec => sec.classList.add("hidden"));
        viewSections.forEach(sec => sec.classList.remove("active"));
        navBtns.forEach(btn => btn.classList.remove("active"));

        const targetSec = document.getElementById(viewId);
        if (targetSec) {
            targetSec.classList.remove("hidden");
            targetSec.classList.add("active");
        }

        const activeNavBtn = document.querySelector(`.nav-btn[data-view="${viewId}"]`);
        if (activeNavBtn) activeNavBtn.classList.add("active");
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    navBtns.forEach(btn => {
        btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    document.querySelectorAll("[data-target-view]").forEach(btn => {
        btn.addEventListener("click", () => switchView(btn.dataset.targetView));
    });

    if (brandHome) {
        brandHome.addEventListener("click", () => switchView("landing-view"));
    }

    // --- Health & Readiness Telemetry ---
    async function checkHealthTelemetry() {
        const start = performance.now();
        try {
            const [hRes, rRes] = await Promise.all([
                fetch("/health"),
                fetch("/ready")
            ]);
            const duration = Math.round(performance.now() - start);

            if (hRes.ok) {
                const hData = await hRes.json();
                statusDot.className = "status-dot online";
                statusText.textContent = "API ONLINE";
                if (dashApiStatus) dashApiStatus.textContent = "ONLINE";
                if (dashLatency) dashLatency.textContent = `${duration} ms`;
                if (dashVersion) dashVersion.textContent = `v${hData.version || '1.0.0'}`;
                if (healthStatusVal) healthStatusVal.textContent = "200 OK (Healthy)";
                if (healthTimeVal) healthTimeVal.textContent = hData.timestamp || new Date().toISOString();
            } else {
                throw new Error("Health non-200");
            }

            if (rRes.ok) {
                const rData = await rRes.json();
                if (dashOcrStatus) dashOcrStatus.textContent = rData.ocr?.tesseract === "available" ? "AVAILABLE" : "LIMITED";
                if (readyStatusVal) readyStatusVal.textContent = "200 OK (Ready)";
            } else {
                if (dashOcrStatus) dashOcrStatus.textContent = "UNAVAILABLE";
                if (readyStatusVal) readyStatusVal.textContent = "503 Unavailable";
            }
        } catch (e) {
            statusDot.className = "status-dot offline";
            statusText.textContent = "API OFFLINE / WAKING";
            if (dashApiStatus) dashApiStatus.textContent = "WAKING / OFFLINE";
            if (healthStatusVal) healthStatusVal.textContent = "Unavailable";
            if (readyStatusVal) readyStatusVal.textContent = "Unavailable";
        }
    }

    checkHealthTelemetry();
    setInterval(checkHealthTelemetry, 60000); // Check telemetry every 60s
    if (btnRefreshHealth) {
        btnRefreshHealth.addEventListener("click", () => {
            checkHealthTelemetry();
            showToast("Refreshing health telemetry...");
        });
    }

    // --- Slider & Upload Events ---
    thresholdSlider.addEventListener("input", (e) => {
        thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
    });

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    btnClearFile.addEventListener("click", (e) => {
        e.stopPropagation();
        clearSelectedFile();
    });

    function handleFileSelect(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        const validExts = ["pdf", "png", "jpg", "jpeg", "tiff", "webp"];
        if (!validExts.includes(ext)) {
            showToast("Unsupported file format. Please upload PDF, PNG, JPG, or WEBP.");
            return;
        }
        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = formatBytes(file.size);
        fileBanner.classList.remove("hidden");
        btnProcess.disabled = false;
        coldStartBanner.classList.add("hidden");
    }

    function clearSelectedFile() {
        selectedFile = null;
        fileInput.value = "";
        fileBanner.classList.add("hidden");
        btnProcess.disabled = true;
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + ['Bytes', 'KB', 'MB', 'GB'][i];
    }

    // --- Deterministic Progress Updates ---
    function updateProgressStage(label, pct) {
        progressStageBar.classList.remove("hidden");
        stageLabel.textContent = label;
        stageProgressFill.style.width = `${pct}%`;
    }

    // --- Primary OCR Request Handler ---
    btnProcess.addEventListener("click", () => runDocumentExtraction());
    btnRetryUpload.addEventListener("click", () => runDocumentExtraction());

    async function runDocumentExtraction() {
        if (!selectedFile) return;

        btnProcess.disabled = true;
        processSpinner.classList.remove("hidden");
        btnProcessText.textContent = "Processing Extraction...";
        coldStartBanner.classList.add("hidden");

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("language", ocrLanguageSelect.value);
        formData.append("engine_name", forceOcrToggle.checked ? "tesseract" : "auto");
        formData.append("extract_tables", extractTablesToggle.checked);
        formData.append("include_provenance", "true");
        formData.append("quality_threshold", thresholdSlider.value);
        if (maxPagesSelect) {
            formData.append("max_pages", maxPagesSelect.value);
        }

        updateProgressStage("Uploading document payload...", 20);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

        try {
            setTimeout(() => updateProgressStage("Profiling layout signals...", 45), 400);
            setTimeout(() => updateProgressStage("Extracting native & OCR text streams...", 70), 900);
            setTimeout(() => updateProgressStage("Parsing table matrices & evaluating quality...", 90), 1400);

            const res = await fetch("/v1/ocr", {
                method: "POST",
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.status === 502 || res.status === 503 || res.status === 504) {
                throw new Error("COLD_START");
            }

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail?.error?.message || errData.detail || "Extraction failed");
            }

            updateProgressStage("Complete!", 100);
            setTimeout(() => progressStageBar.classList.add("hidden"), 800);

            currentDocument = await res.json();
            showToast("Document processed successfully!");
            retryCount = 0;

            renderResultsWorkspace();
            workspaceResults.classList.remove("hidden");
            workspaceResults.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            clearTimeout(timeoutId);
            progressStageBar.classList.add("hidden");
            if (err.name === "AbortError") {
                showToast("Request timed out (90s). Try selecting a lower Max Pages limit (e.g. 10 or 25 pages).", 6000);
            } else if (err.message === "COLD_START") {
                coldStartBanner.classList.remove("hidden");
                showToast("Server is waking up. Please click 'Retry Now'.", 5000);
            } else {
                showToast(`Error: ${err.message}`);
            }
        } finally {
            btnProcess.disabled = false;
            processSpinner.classList.add("hidden");
            btnProcessText.textContent = "Run Extraction Pipeline";
        }
    }

    // --- Render Results Workspace ---
    function renderResultsWorkspace() {
        if (!currentDocument) return;

        currentPageIndex = 0;

        // Meta Card
        metaDocId.textContent = (currentDocument.document_id || '').slice(0, 8) + "...";
        metaFilename.textContent = currentDocument.filename || selectedFile?.name || "document.pdf";
        metaTotalPages.textContent = currentDocument.total_pages || (currentDocument.pages ? currentDocument.pages.length : 1);

        const qScore = currentDocument.quality?.overall_score || 0.95;
        metaQualityBadge.textContent = `${(qScore * 100).toFixed(0)}%`;

        // Gauges
        const scanScore = currentDocument.quality?.scan_likelihood || 0.1;
        const scanPct = Math.round(scanScore * 100);
        gaugeScanPercent.textContent = `${scanPct}%`;
        gaugeScanFill.style.width = `${scanPct}%`;
        gaugeScanRec.textContent = scanScore > 0.5 ? "Route: Tesseract OCR" : "Route: Native Vector";

        // Tab Badges
        tableCountBadge.textContent = currentDocument.tables ? currentDocument.tables.length : 0;

        // Text View
        extractedTextView.value = currentDocument.text || "";
        updateTextStats(currentDocument.text || "");

        // Full JSON View
        fullJsonView.value = JSON.stringify(currentDocument, null, 2);

        // Quality Tab
        qOverall.textContent = qScore.toFixed(2);
        qOcrConf.textContent = `${((currentDocument.quality?.ocr_confidence || 0) * 100).toFixed(1)}%`;
        qGarbage.textContent = `${((currentDocument.quality?.garbage_ratio || 0) * 100).toFixed(1)}%`;

        renderPagesTab();
        renderProvenanceLog();
        renderTableDropdown();

        // Render Canvas
        renderPage(currentPageIndex);
    }

    // --- Page Navigator & Canvas ---
    btnPrevPage.addEventListener("click", () => {
        if (currentPageIndex > 0) {
            currentPageIndex--;
            renderPage(currentPageIndex);
        }
    });

    btnNextPage.addEventListener("click", () => {
        if (currentDocument && currentDocument.pages && currentPageIndex < currentDocument.pages.length - 1) {
            currentPageIndex++;
            renderPage(currentPageIndex);
        }
    });

    function renderPage(pageIdx) {
        if (!currentDocument || !currentDocument.pages || !currentDocument.pages[pageIdx]) return;
        const page = currentDocument.pages[pageIdx];

        pageIndicator.textContent = `Page ${pageIdx + 1} of ${currentDocument.total_pages || currentDocument.pages.length}`;
        pageRouteBadge.textContent = page.extraction_method || "native";

        drawPageCanvas(page);
    }

    function drawPageCanvas(page) {
        const ctx = pageCanvas.getContext("2d");
        const width = page.width || 612;
        const height = page.height || 792;

        pageCanvas.width = width;
        pageCanvas.height = height;

        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        if (page.provenance) {
            page.provenance.forEach(rec => {
                const [x0, y0, x1, y1] = rec.bbox || [0, 0, width, height];
                const isOcr = rec.extraction_method === "ocr";

                ctx.fillStyle = isOcr ? "rgba(16, 185, 129, 0.08)" : "rgba(59, 130, 246, 0.08)";
                ctx.fillRect(x0, y0, x1 - x0, y1 - y0);

                ctx.strokeStyle = isOcr ? "#10b981" : "#3b82f6";
                ctx.lineWidth = 1.2;
                ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
            });
        }
    }

    // --- Pages List Tab ---
    function renderPagesTab() {
        pagesListContainer.innerHTML = "";
        if (!currentDocument || !currentDocument.pages) return;

        currentDocument.pages.forEach((p, idx) => {
            const card = document.createElement("div");
            card.className = "card glass-card feature-card";
            card.style.padding = "1rem";
            card.innerHTML = `
                <h4>Page ${p.page_number} (${p.extraction_method || 'native'})</h4>
                <p style="font-size: 0.82rem; color: var(--text-muted);">${(p.text || '').slice(0, 150)}...</p>
            `;
            pagesListContainer.appendChild(card);
        });
    }

    // --- Text Stats & Copy Utilities ---
    function updateTextStats(txt) {
        statChars.textContent = `${txt.length} Chars`;
        const words = txt.trim().split(/\s+/).filter(w => w.length > 0).length;
        statWords.textContent = `${words} Words`;
    }

    btnCopyText.addEventListener("click", () => {
        navigator.clipboard.writeText(extractedTextView.value);
        showToast("Full text copied to clipboard!");
    });

    btnCopyJson.addEventListener("click", () => {
        navigator.clipboard.writeText(fullJsonView.value);
        showToast("Full JSON payload copied to clipboard!");
    });

    // --- Table Inspector ---
    function renderTableDropdown() {
        tableSelectDropdown.innerHTML = "";
        const tables = currentDocument.tables || [];

        if (tables.length === 0) {
            tableSelectDropdown.innerHTML = `<option value="">No tables detected</option>`;
            tableMatrixContainer.innerHTML = `<p class="placeholder-text">No 2D table matrices extracted in this document.</p>`;
            return;
        }

        tables.forEach((tbl, idx) => {
            const opt = document.createElement("option");
            opt.value = idx;
            opt.textContent = `Table ${idx + 1} (${tbl.row_count}x${tbl.column_count})`;
            tableSelectDropdown.appendChild(opt);
        });

        tableSelectDropdown.dataset.tables = JSON.stringify(tables);
        renderTableMatrix(0);
    }

    tableSelectDropdown.addEventListener("change", (e) => {
        renderTableMatrix(parseInt(e.target.value));
    });

    function renderTableMatrix(index) {
        const rawData = tableSelectDropdown.dataset.tables;
        if (!rawData) return;
        const tables = JSON.parse(rawData);
        if (!tables[index]) return;

        const matrix = tables[index].matrix || [];
        let html = `<table class="matrix-table">`;
        matrix.forEach((row, rIdx) => {
            html += `<tr>`;
            row.forEach(cell => {
                html += rIdx === 0 ? `<th>${escapeHtml(cell)}</th>` : `<td>${escapeHtml(cell)}</td>`;
            });
            html += `</tr>`;
        });
        html += `</table>`;
        tableMatrixContainer.innerHTML = html;
    }

    function escapeHtml(str) {
        return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    btnCopyTableCsv.addEventListener("click", () => {
        const rawData = tableSelectDropdown.dataset.tables;
        if (!rawData) return;
        const index = parseInt(tableSelectDropdown.value || "0");
        const tables = JSON.parse(rawData);
        if (tables[index]) {
            const matrix = tables[index].matrix || [];
            const csv = matrix.map(row => row.map(cell => `"${(cell||'').replace(/"/g, '""')}"`).join(",")).join("\n");
            navigator.clipboard.writeText(csv);
            showToast("Table CSV copied to clipboard!");
        }
    });

    // --- Spatial Provenance Stream ---
    function renderProvenanceLog() {
        provenanceTableBody.innerHTML = "";
        const provList = currentDocument.provenance || [];

        provList.forEach((rec, idx) => {
            const tr = document.createElement("tr");
            const bboxStr = rec.bbox ? `[${rec.bbox.map(n => Math.round(n)).join(", ")}]` : "N/A";
            const confPct = `${((rec.confidence || 1) * 100).toFixed(0)}%`;
            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td><code class="code-font">${bboxStr}</code></td>
                <td><span class="badge badge-route">${rec.engine || 'native'}</span></td>
                <td>${confPct}</td>
                <td>${escapeHtml((rec.text_snippet || '').slice(0, 50))}</td>
            `;
            provenanceTableBody.appendChild(tr);
        });

        if (provList.length === 0) {
            provenanceTableBody.innerHTML = `<tr><td colspan="5" class="placeholder-text">No provenance records loaded.</td></tr>`;
        }
    }

    // --- Tabs Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });

    // --- API Code Snippet Generator ---
    apiEpItems.forEach(item => {
        item.addEventListener("click", () => {
            apiEpItems.forEach(i => i.classList.remove("active"));
            item.classList.add("active");
            activeApiEndpoint = item.dataset.ep;
            updateApiCodeSnippet();
        });
    });

    langTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            langTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeApiLang = tab.dataset.lang;
            updateApiCodeSnippet();
        });
    });

    function updateApiCodeSnippet() {
        const host = window.location.origin.includes("localhost") 
            ? window.location.origin 
            : "https://YOUR-DOCROUTE-BACKEND.onrender.com";

        const docId = currentDocument ? currentDocument.document_id : "DOC_ID_HERE";

        const snippets = {
            ocr: {
                curl: `curl -X 'POST' \\\n  '${host}/v1/ocr' \\\n  -F 'file=@/path/to/invoice.pdf' \\\n  -F 'language=eng+hin' \\\n  -F 'extract_tables=true'`,
                python: `import requests\n\nurl = "${host}/v1/ocr"\nfiles = {"file": open("invoice.pdf", "rb")}\ndata = {\n    "language": "eng+hin",\n    "extract_tables": True\n}\n\nresponse = requests.post(url, files=files, data=data)\nprint(response.json())`,
                js: `const formData = new FormData();\nformData.append("file", fileInputElement.files[0]);\nformData.append("language", "eng+hin");\n\nconst res = await fetch("${host}/v1/ocr", {\n    method: "POST",\n    body: formData\n});\nconst data = await res.json();\nconsole.log(data);`
            },
            documents: {
                curl: `curl -X 'POST' \\\n  '${host}/v1/documents?ocr_threshold=0.5' \\\n  -F 'file=@document.pdf'`,
                python: `import requests\n\nurl = "${host}/v1/documents"\nfiles = {"file": open("document.pdf", "rb")}\nres = requests.post(url, files=files, params={"ocr_threshold": 0.5})\nprint(res.json())`,
                js: `const formData = new FormData();\nformData.append("file", fileInputElement.files[0]);\nconst res = await fetch("${host}/v1/documents", {\n    method: "POST",\n    body: formData\n});\nconsole.log(await res.json());`
            },
            "get-doc": {
                curl: `curl -X 'GET' '${host}/v1/documents/${docId}'`,
                python: `import requests\n\nres = requests.get("${host}/v1/documents/${docId}")\nprint(res.json())`,
                js: `const res = await fetch("${host}/v1/documents/${docId}");\nconsole.log(await res.json());`
            },
            "get-vision": {
                curl: `curl -X 'GET' '${host}/v1/documents/${docId}/vision'`,
                python: `import requests\n\nres = requests.get("${host}/v1/documents/${docId}/vision")\nprint(res.json())`,
                js: `const res = await fetch("${host}/v1/documents/${docId}/vision");\nconsole.log(await res.json());`
            }
        };

        const currentEp = snippets[activeApiEndpoint] || snippets["ocr"];
        apiCodeContent.textContent = currentEp[activeApiLang] || currentEp["curl"];
    }

    btnCopyCode.addEventListener("click", () => {
        navigator.clipboard.writeText(apiCodeContent.textContent);
        showToast("Code snippet copied to clipboard!");
    });

    updateApiCodeSnippet();
});

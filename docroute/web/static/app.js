/**
 * DocRoute - Adaptive Document Intelligence Dashboard JS Client
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- State Variables ---
    let selectedFile = null;
    let currentDocument = null; // StructuredDocument payload
    let currentProfile = null;  // DocumentProfile payload
    let currentPageIndex = 0;   // 0-indexed
    let activeApiEndpoint = "upload";
    let activeApiLang = "curl";

    // --- DOM Elements ---
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const fileBanner = document.getElementById("file-banner");
    const selectedFileName = document.getElementById("selected-file-name");
    const selectedFileSize = document.getElementById("selected-file-size");
    const btnClearFile = document.getElementById("btn-clear-file");

    const thresholdSlider = document.getElementById("ocr-threshold-slider");
    const thresholdVal = document.getElementById("ocr-threshold-val");
    const ocrLanguageSelect = document.getElementById("ocr-language-select");
    const forceOcrToggle = document.getElementById("force-ocr-toggle");
    const extractTablesToggle = document.getElementById("extract-tables-toggle");

    const btnProcess = document.getElementById("btn-process");
    const btnProcessText = document.getElementById("btn-process-text");
    const processSpinner = document.getElementById("process-spinner");

    const workspaceSection = document.getElementById("workspace-section");
    
    // Sidebar DOM
    const metaDocId = document.getElementById("meta-doc-id");
    const metaFilename = document.getElementById("meta-filename");
    const metaTotalPages = document.getElementById("meta-total-pages");
    const metaQualityBadge = document.getElementById("meta-quality-badge");

    const gaugeScanPercent = document.getElementById("gauge-scan-percent");
    const gaugeScanFill = document.getElementById("gauge-scan-fill");
    const gaugeScanRec = document.getElementById("gauge-scan-recommendation");
    const gaugeQualityPercent = document.getElementById("gauge-quality-percent");
    const gaugeQualityFill = document.getElementById("gauge-quality-fill");
    const gaugeQualityStatus = document.getElementById("gauge-quality-status");

    const btnPrevPage = document.getElementById("btn-prev-page");
    const btnNextPage = document.getElementById("btn-next-page");
    const pageIndicator = document.getElementById("page-indicator");
    const pageRouteBadge = document.getElementById("page-route-badge");

    // Inspector Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // Canvas DOM
    const pageCanvas = document.getElementById("page-canvas");
    const bboxTooltip = document.getElementById("bbox-tooltip");
    const chkShowWords = document.getElementById("chk-show-words");
    const chkShowTables = document.getElementById("chk-show-tables");

    // Debug Image DOM
    const debugOverlayImg = document.getElementById("debug-overlay-img");
    const btnDownloadDebug = document.getElementById("btn-download-debug");

    // Text DOM
    const extractedTextView = document.getElementById("extracted-text-view");
    const statChars = document.getElementById("stat-chars");
    const statWords = document.getElementById("stat-words");
    const statLines = document.getElementById("stat-lines");
    const btnCopyText = document.getElementById("btn-copy-text");

    // Table Matrix DOM
    const tableCountBadge = document.getElementById("table-count-badge");
    const tableSelectDropdown = document.getElementById("table-select-dropdown");
    const tableMatrixContainer = document.getElementById("table-matrix-container");
    const btnCopyTableJson = document.getElementById("btn-copy-table-json");
    const btnCopyTableCsv = document.getElementById("btn-copy-table-csv");

    // Provenance DOM
    const qOverall = document.getElementById("q-overall");
    const qOcrConf = document.getElementById("q-ocr-conf");
    const qDensity = document.getElementById("q-density");
    const qGarbage = document.getElementById("q-garbage");
    const provenanceTableBody = document.querySelector("#provenance-table tbody");

    // API Code Snippets DOM
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
        setTimeout(() => {
            toast.remove();
        }, duration);
    }

    // --- Slider Event ---
    thresholdSlider.addEventListener("input", (e) => {
        thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
    });

    // --- File Drag & Drop Events ---
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
    });
    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("drag-over");
    });
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
            showToast("Invalid file format. Please upload PDF or image.");
            return;
        }
        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = formatBytes(file.size);
        fileBanner.classList.remove("hidden");
        btnProcess.disabled = false;
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
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // --- Process Document Request ---
    btnProcess.addEventListener("click", async () => {
        if (!selectedFile) return;

        btnProcess.disabled = true;
        processSpinner.classList.remove("hidden");
        btnProcessText.textContent = "Processing Engine...";

        const formData = new FormData();
        formData.append("file", selectedFile);

        const params = new URLSearchParams({
            ocr_threshold: thresholdSlider.value,
            force_ocr: forceOcrToggle.checked,
            language: ocrLanguageSelect.value,
            extract_tables: extractTablesToggle.checked
        });

        try {
            const res = await fetch(`/documents?${params.toString()}`, {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Document processing failed");
            }

            currentDocument = await res.json();
            showToast("Document processed successfully!");

            // Fetch document profile as well
            try {
                const profRes = await fetch(`/documents/${currentDocument.document_id}/profile`);
                if (profRes.ok) {
                    currentProfile = await profRes.json();
                }
            } catch (pErr) {
                console.warn("Could not fetch document profile:", pErr);
            }

            renderDocumentIntelligence();
            workspaceSection.classList.remove("hidden");
            workspaceSection.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            showToast(`Error: ${err.message}`);
        } finally {
            btnProcess.disabled = false;
            processSpinner.classList.add("hidden");
            btnProcessText.textContent = "Process Document";
        }
    });

    // --- Render Main Workspace UI ---
    function renderDocumentIntelligence() {
        if (!currentDocument) return;

        currentPageIndex = 0;

        // Meta Card
        metaDocId.textContent = currentDocument.document_id.slice(0, 8) + "...";
        metaDocId.title = currentDocument.document_id;
        metaFilename.textContent = currentDocument.filename;
        metaTotalPages.textContent = currentDocument.total_pages;

        const qScore = currentDocument.overall_quality.overall_score || 0;
        metaQualityBadge.textContent = `${(qScore * 100).toFixed(0)}%`;
        if (qScore > 0.8) {
            metaQualityBadge.className = "meta-val badge badge-route";
        } else {
            metaQualityBadge.className = "meta-val badge badge-version";
        }

        // Gauges
        const scanScore = currentProfile ? currentProfile.scan_likelihood_score : (currentDocument.overall_quality.scan_likelihood || 0);
        const scanPct = Math.round(scanScore * 100);
        gaugeScanPercent.textContent = `${scanPct}%`;
        gaugeScanFill.style.width = `${scanPct}%`;
        gaugeScanRec.textContent = scanScore > 0.5 ? "Route: OCR Engine" : "Route: Vector Native";

        const qualPct = (qScore * 100).toFixed(1);
        gaugeQualityPercent.textContent = qScore.toFixed(2);
        gaugeQualityFill.style.width = `${qualPct}%`;
        gaugeQualityStatus.textContent = qScore > 0.75 ? "Confidence: High" : "Confidence: Moderate";

        // Tab Tables Badge Count
        let totalTables = 0;
        currentDocument.pages.forEach(p => totalTables += (p.tables ? p.tables.length : 0));
        tableCountBadge.textContent = totalTables;

        // Text Tab aggregated text
        let fullText = currentDocument.pages.map((p, idx) => `--- Page ${idx + 1} ---\n\n${p.text}`).join("\n\n");
        extractedTextView.value = fullText;
        updateTextStats(fullText);

        // Quality & Provenance Tab
        qOverall.textContent = qScore.toFixed(2);
        qOcrConf.textContent = `${((currentDocument.overall_quality.ocr_confidence || 0) * 100).toFixed(1)}%`;
        qDensity.textContent = (currentDocument.overall_quality.formatting_density || 0).toFixed(2);
        qGarbage.textContent = `${((currentDocument.overall_quality.garbage_character_ratio || 0) * 100).toFixed(1)}%`;

        renderProvenanceLog();
        renderTableDropdown();

        // Render Page Canvas & Debug Img
        renderPage(currentPageIndex);
        updateApiCodeSnippet();
    }

    // --- Page Navigator ---
    btnPrevPage.addEventListener("click", () => {
        if (currentPageIndex > 0) {
            currentPageIndex--;
            renderPage(currentPageIndex);
        }
    });

    btnNextPage.addEventListener("click", () => {
        if (currentDocument && currentPageIndex < currentDocument.pages.length - 1) {
            currentPageIndex++;
            renderPage(currentPageIndex);
        }
    });

    function renderPage(pageIdx) {
        if (!currentDocument || !currentDocument.pages[pageIdx]) return;
        const page = currentDocument.pages[pageIdx];

        pageIndicator.textContent = `Page ${pageIdx + 1} of ${currentDocument.total_pages}`;
        pageRouteBadge.textContent = page.route_used || "native";

        // Render Canvas
        drawPageCanvas(page);

        // Render Debug PNG stream link
        const debugUrl = `/documents/${currentDocument.document_id}/debug/${pageIdx + 1}`;
        debugOverlayImg.src = debugUrl;
        btnDownloadDebug.href = debugUrl;
    }

    // --- Canvas Bounding Box Rendering ---
    function drawPageCanvas(page) {
        const ctx = pageCanvas.getContext("2d");
        const width = page.width || 612;
        const height = page.height || 792;

        pageCanvas.width = width;
        pageCanvas.height = height;

        ctx.clearRect(0, 0, width, height);

        // White background
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        // Render Blocks & Words
        if (page.blocks) {
            page.blocks.forEach(block => {
                const [x0, y0, x1, y1] = block.bbox;
                const isOcr = block.source === "tesseract";

                // Block background
                ctx.fillStyle = isOcr ? "rgba(16, 185, 129, 0.08)" : "rgba(59, 130, 246, 0.08)";
                ctx.fillRect(x0, y0, x1 - x0, y1 - y0);

                // Block Border
                ctx.strokeStyle = isOcr ? "#10b981" : "#3b82f6";
                ctx.lineWidth = 1.5;
                ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);

                // Draw text inside block
                ctx.fillStyle = "#0f172a";
                ctx.font = "12px sans-serif";
                
                // Words
                if (chkShowWords.checked && block.lines) {
                    block.lines.forEach(line => {
                        if (line.words) {
                            line.words.forEach(w => {
                                const [wx0, wy0, wx1, wy1] = w.bbox;
                                ctx.strokeStyle = isOcr ? "rgba(16, 185, 129, 0.4)" : "rgba(59, 130, 246, 0.4)";
                                ctx.lineWidth = 0.8;
                                ctx.strokeRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
                            });
                        }
                    });
                }
            });
        }

        // Render Tables
        if (chkShowTables.checked && page.tables) {
            page.tables.forEach(tbl => {
                const [tx0, ty0, tx1, ty1] = tbl.bbox;
                ctx.fillStyle = "rgba(168, 85, 247, 0.15)";
                ctx.fillRect(tx0, ty0, tx1 - tx0, ty1 - ty0);

                ctx.strokeStyle = "#a855f7";
                ctx.lineWidth = 2.5;
                ctx.strokeRect(tx0, ty0, tx1 - tx0, ty1 - ty0);

                // Render Cells
                if (tbl.cells) {
                    tbl.cells.forEach(cell => {
                        const [cx0, cy0, cx1, cy1] = cell.bbox;
                        ctx.strokeStyle = "rgba(168, 85, 247, 0.6)";
                        ctx.lineWidth = 1;
                        ctx.strokeRect(cx0, cy0, cx1 - cx0, cy1 - cy0);
                    });
                }
            });
        }
    }

    // Canvas Checkbox Toggles
    chkShowWords.addEventListener("change", () => {
        if (currentDocument) renderPage(currentPageIndex);
    });
    chkShowTables.addEventListener("change", () => {
        if (currentDocument) renderPage(currentPageIndex);
    });

    // Canvas Mouseover Tooltip
    pageCanvas.addEventListener("mousemove", (e) => {
        if (!currentDocument || !currentDocument.pages[currentPageIndex]) return;

        const rect = pageCanvas.getBoundingClientRect();
        const scaleX = pageCanvas.width / rect.width;
        const scaleY = pageCanvas.height / rect.height;

        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;

        const page = currentDocument.pages[currentPageIndex];
        let foundBlock = null;

        if (page.blocks) {
            for (let b of page.blocks) {
                const [x0, y0, x1, y1] = b.bbox;
                if (mouseX >= x0 && mouseX <= x1 && mouseY >= y0 && mouseY <= y1) {
                    foundBlock = b;
                    break;
                }
            }
        }

        if (foundBlock) {
            bboxTooltip.style.left = `${e.clientX - rect.left + 15}px`;
            bboxTooltip.style.top = `${e.clientY - rect.top + 15}px`;
            bboxTooltip.innerHTML = `
                <strong>Source:</strong> ${foundBlock.source || 'native'}<br>
                <strong>Confidence:</strong> ${((foundBlock.confidence || 1) * 100).toFixed(0)}%<br>
                <strong>Text:</strong> ${(foundBlock.text || '').slice(0, 80)}...
            `;
            bboxTooltip.classList.remove("hidden");
        } else {
            bboxTooltip.classList.add("hidden");
        }
    });

    pageCanvas.addEventListener("mouseleave", () => {
        bboxTooltip.classList.add("hidden");
    });

    // --- Extracted Text View Utilities ---
    function updateTextStats(txt) {
        statChars.textContent = `${txt.length} Chars`;
        const words = txt.trim().split(/\s+/).filter(w => w.length > 0).length;
        statWords.textContent = `${words} Words`;
        const lines = txt.split(/\r\n|\r|\n/).length;
        statLines.textContent = `${lines} Lines`;
    }

    btnCopyText.addEventListener("click", () => {
        navigator.clipboard.writeText(extractedTextView.value);
        showToast("Full text copied to clipboard!");
    });

    // --- Table Matrix Inspector ---
    function renderTableDropdown() {
        tableSelectDropdown.innerHTML = "";
        let tableList = [];

        currentDocument.pages.forEach((page, pIdx) => {
            if (page.tables) {
                page.tables.forEach((tbl, tIdx) => {
                    tableList.push({
                        page_num: pIdx + 1,
                        table_index: tIdx,
                        table: tbl
                    });
                });
            }
        });

        if (tableList.length === 0) {
            tableSelectDropdown.innerHTML = `<option value="">No tables detected</option>`;
            tableMatrixContainer.innerHTML = `<p class="placeholder-text">No structured tables extracted in this document.</p>`;
            return;
        }

        tableList.forEach((item, idx) => {
            const opt = document.createElement("option");
            opt.value = idx;
            opt.textContent = `Page ${item.page_num} - Table ${item.table_index + 1} (${item.table.row_count}x${item.table.column_count})`;
            tableSelectDropdown.appendChild(opt);
        });

        tableSelectDropdown.dataset.tables = JSON.stringify(tableList);
        renderTableMatrix(0);
    }

    tableSelectDropdown.addEventListener("change", (e) => {
        renderTableMatrix(parseInt(e.target.value));
    });

    function renderTableMatrix(index) {
        const rawData = tableSelectDropdown.dataset.tables;
        if (!rawData) return;
        const tableList = JSON.parse(rawData);
        if (!tableList[index]) return;

        const tblObj = tableList[index].table;
        const matrix = tblObj.matrix || [];

        if (matrix.length === 0) {
            tableMatrixContainer.innerHTML = `<p class="placeholder-text">Empty table matrix.</p>`;
            return;
        }

        let html = `<table class="matrix-table">`;
        matrix.forEach((row, rIdx) => {
            html += `<tr>`;
            row.forEach(cellText => {
                if (rIdx === 0) {
                    html += `<th>${escapeHtml(cellText)}</th>`;
                } else {
                    html += `<td>${escapeHtml(cellText)}</td>`;
                }
            });
            html += `</tr>`;
        });
        html += `</table>`;
        tableMatrixContainer.innerHTML = html;
    }

    function escapeHtml(str) {
        return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    btnCopyTableJson.addEventListener("click", () => {
        const rawData = tableSelectDropdown.dataset.tables;
        if (!rawData) return;
        const index = parseInt(tableSelectDropdown.value || "0");
        const tableList = JSON.parse(rawData);
        if (tableList[index]) {
            navigator.clipboard.writeText(JSON.stringify(tableList[index].table, null, 2));
            showToast("Table JSON copied to clipboard!");
        }
    });

    btnCopyTableCsv.addEventListener("click", () => {
        const rawData = tableSelectDropdown.dataset.tables;
        if (!rawData) return;
        const index = parseInt(tableSelectDropdown.value || "0");
        const tableList = JSON.parse(rawData);
        if (tableList[index]) {
            const matrix = tableList[index].table.matrix || [];
            const csv = matrix.map(row => row.map(cell => `"${(cell||'').replace(/"/g, '""')}"`).join(",")).join("\n");
            navigator.clipboard.writeText(csv);
            showToast("Table CSV copied to clipboard!");
        }
    });

    // --- Spatial Provenance Stream ---
    function renderProvenanceLog() {
        provenanceTableBody.innerHTML = "";
        let lineCount = 0;

        currentDocument.pages.forEach(p => {
            if (p.blocks) {
                p.blocks.forEach(b => {
                    if (b.lines) {
                        b.lines.forEach(l => {
                            lineCount++;
                            const tr = document.createElement("tr");
                            const bboxStr = l.bbox ? `[${l.bbox.map(n => Math.round(n)).join(", ")}]` : "N/A";
                            const confPct = `${((l.confidence || b.confidence || 1) * 100).toFixed(0)}%`;
                            
                            tr.innerHTML = `
                                <td>${lineCount}</td>
                                <td><code class="code-font">${bboxStr}</code></td>
                                <td><span class="badge ${b.source === 'tesseract' ? 'badge-version' : 'badge-route'}">${b.source || 'native'}</span></td>
                                <td>${confPct}</td>
                                <td>${escapeHtml((l.text || '').slice(0, 60))}</td>
                            `;
                            provenanceTableBody.appendChild(tr);
                        });
                    }
                });
            }
        });

        if (lineCount === 0) {
            provenanceTableBody.innerHTML = `<tr><td colspan="5" class="placeholder-text">No provenance lines found.</td></tr>`;
        }
    }

    // --- Tabs Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.dataset.tab;
            document.getElementById(target).classList.add("active");
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
        const docId = currentDocument ? currentDocument.document_id : "DOC_ID_HERE";
        const host = window.location.origin;

        const snippets = {
            upload: {
                curl: `curl -X 'POST' \\\n  '${host}/documents?ocr_threshold=0.5&force_ocr=false&language=eng%2Bhin&extract_tables=true' \\\n  -H 'accept: application/json' \\\n  -H 'Content-Type: multipart/form-data' \\\n  -F 'file=@/path/to/invoice.pdf'`,
                python: `import requests\n\nurl = "${host}/documents"\nfiles = {"file": open("/path/to/invoice.pdf", "rb")}\nparams = {\n    "ocr_threshold": 0.5,\n    "force_ocr": False,\n    "language": "eng+hin",\n    "extract_tables": True\n}\n\nresponse = requests.post(url, files=files, params=params)\nprint(response.json())`,
                js: `const formData = new FormData();\nformData.append("file", fileInputElement.files[0]);\n\nconst response = await fetch("${host}/documents?ocr_threshold=0.5&language=eng+hin", {\n    method: "POST",\n    body: formData\n});\nconst structuredDoc = await response.json();\nconsole.log(structuredDoc);`,
                node: `const axios = require('axios');\nconst FormData = require('form-data');\nconst fs = require('fs');\n\nconst form = new FormData();\nform.append('file', fs.createReadStream('/path/to/invoice.pdf'));\n\naxios.post('${host}/documents', form, {\n    headers: form.getHeaders()\n}).then(res => console.log(res.data));`
            },
            "get-doc": {
                curl: `curl -X 'GET' '${host}/documents/${docId}' -H 'accept: application/json'`,
                python: `import requests\n\nresponse = requests.get("${host}/documents/${docId}")\ndoc = response.json()\nprint(f"Total Pages: {doc['total_pages']}")`,
                js: `const res = await fetch("${host}/documents/${docId}");\nconst doc = await res.json();\nconsole.log(doc);`,
                node: `const axios = require('axios');\n\naxios.get('${host}/documents/${docId}')\n  .then(res => console.log(res.data));`
            },
            "get-profile": {
                curl: `curl -X 'GET' '${host}/documents/${docId}/profile' -H 'accept: application/json'`,
                python: `import requests\n\nresponse = requests.get("${host}/documents/${docId}/profile")\nprofile = response.json()\nprint(f"Scan Likelihood: {profile['scan_likelihood_score']}")`,
                js: `const res = await fetch("${host}/documents/${docId}/profile");\nconst profile = await res.json();\nconsole.log("Is Scanned:", profile.is_scanned);`,
                node: `const axios = require('axios');\n\naxios.get('${host}/documents/${docId}/profile')\n  .then(res => console.log(res.data));`
            },
            "get-text": {
                curl: `curl -X 'GET' '${host}/documents/${docId}/text' -H 'accept: application/json'`,
                python: `import requests\n\nresponse = requests.get("${host}/documents/${docId}/text")\ntext_data = response.json()\nprint(text_data['text'])`,
                js: `const res = await fetch("${host}/documents/${docId}/text");\nconst { text } = await res.json();\nconsole.log(text);`,
                node: `const axios = require('axios');\n\naxios.get('${host}/documents/${docId}/text')\n  .then(res => console.log(res.data.text));`
            },
            "get-tables": {
                curl: `curl -X 'GET' '${host}/documents/${docId}/tables' -H 'accept: application/json'`,
                python: `import requests\n\nresponse = requests.get("${host}/documents/${docId}/tables")\ntables = response.json()\nfor t in tables:\n    print(f"Table Matrix ({t['row_count']}x{t['column_count']}):", t['matrix'])`,
                js: `const res = await fetch("${host}/documents/${docId}/tables");\nconst tables = await res.json();\nconsole.log(tables);`,
                node: `const axios = require('axios');\n\naxios.get('${host}/documents/${docId}/tables')\n  .then(res => console.log(res.data));`
            },
            "get-debug": {
                curl: `curl -X 'GET' '${host}/documents/${docId}/debug/1' --output debug_page1.png`,
                python: `import requests\n\nresponse = requests.get("${host}/documents/${docId}/debug/1")\nwith open("debug_page1.png", "wb") as f:\n    f.write(response.content)`,
                js: `const res = await fetch("${host}/documents/${docId}/debug/1");\nconst imageBlob = await res.blob();\nconst imageObjectUrl = URL.createObjectURL(imageBlob);`,
                node: `const axios = require('axios');\nconst fs = require('fs');\n\naxios.get('${host}/documents/${docId}/debug/1', { responseType: 'arraybuffer' })\n  .then(res => fs.writeFileSync('debug_p1.png', res.data));`
            }
        };

        const currentEp = snippets[activeApiEndpoint] || snippets["upload"];
        apiCodeContent.textContent = currentEp[activeApiLang] || currentEp["curl"];
    }

    btnCopyCode.addEventListener("click", () => {
        navigator.clipboard.writeText(apiCodeContent.textContent);
        showToast("Code snippet copied to clipboard!");
    });
});

document.addEventListener('DOMContentLoaded', async () => {
    // ── Elements ────────────────────────────────────────────────────────────
    const homeTab        = document.getElementById('homeTab');
    const historyTab     = document.getElementById('historyTab');
    const homeView       = document.getElementById('homeView');
    const historyView    = document.getElementById('historyView');
    const historyList    = document.getElementById('historyList');

    const siteStatusCard = document.getElementById('siteStatusCard');
    const siteIcon       = document.getElementById('siteIcon');
    const siteStatusText = document.getElementById('siteStatusText');
    const siteStatusDesc = document.getElementById('siteStatusDesc');
    const analysisDetails= document.getElementById('analysisDetails');
    const reasonsList    = document.getElementById('reasonsList');
    const whitelistBtn   = document.getElementById('whitelistBtn');
    const blacklistBtn   = document.getElementById('blacklistBtn');

    const textInput      = document.getElementById('textInput');
    const checkBtn       = document.getElementById('checkBtn');
    const manualResult   = document.getElementById('manualResult');
    const manualStatusText = document.getElementById('manualStatusText');
    const manualReportArea = document.getElementById('manualReportArea');

    const scanScreenBtn  = document.getElementById('scanScreenBtn');
    const cvResult       = document.getElementById('cvResult');
    const cvStatusText   = document.getElementById('cvStatusText');
    const cvContentText  = document.getElementById('cvContentText');
    const cvReportArea   = document.getElementById('cvReportArea');

    // ── Tab Switching ────────────────────────────────────────────────────────
    homeTab.addEventListener('click', () => {
        homeView.style.display = 'block';
        historyView.style.display = 'none';
        homeTab.style.background = 'var(--glass)';
        historyTab.style.background = 'transparent';
    });

    historyTab.addEventListener('click', () => {
        homeView.style.display = 'none';
        historyView.style.display = 'block';
        historyTab.style.background = 'var(--glass)';
        homeTab.style.background = 'transparent';
        loadHistory();
    });

    // ── 1. Phân tích URL tab hiện tại ───────────────────────────────────────
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
        chrome.storage.local.get([`analysis_${tab.id}`], (result) => {
            const data = result[`analysis_${tab.id}`];
            if (data) {
                updateSiteUI(data);
            } else {
                siteStatusText.innerText = 'Chưa có dữ liệu';
                siteStatusDesc.innerText = 'Hãy load lại trang hoặc đợi phân tích';
            }
        });
    }

    function updateSiteUI(data) {
        siteStatusCard.classList.remove('status-safe', 'status-warning', 'status-dangerous');
        if (data.status_code === 'dangerous') {
            siteStatusCard.classList.add('status-dangerous');
            siteIcon.innerText = '🚫';
            siteStatusText.innerText = 'NGUY HIỂM';
            siteStatusDesc.innerText = 'Trang web này có dấu hiệu lừa đảo cao!';
        } else if (data.status_code === 'suspicious') {
            siteStatusCard.classList.add('status-warning');
            siteIcon.innerText = '⚠️';
            siteStatusText.innerText = 'NGHI NGỜ';
            siteStatusDesc.innerText = 'Hãy cẩn thận khi nhập thông tin tại đây.';
        } else {
            siteStatusCard.classList.add('status-safe');
            siteIcon.innerText = '✅';
            siteStatusText.innerText = 'AN TOÀN';
            siteStatusDesc.innerText = 'Không phát hiện dấu hiệu bất thường.';
        }
        if (data.reasons && data.reasons.length > 0) {
            analysisDetails.style.display = 'block';
            reasonsList.innerHTML = data.reasons.map(r => `<div class="reason-item">${r}</div>`).join('');
        }
    }

    // ── 2. Whitelist / Blacklist ─────────────────────────────────────────────
    whitelistBtn.addEventListener('click', async () => {
        if (!tab) return;
        const hostname = new URL(tab.url).hostname;
        chrome.storage.local.get(['whitelist'], (res) => {
            const list = res.whitelist || [];
            if (!list.includes(hostname)) {
                list.push(hostname);
                chrome.storage.local.set({ whitelist: list }, () => {
                    alert(`Đã thêm ${hostname} vào danh sách tin tưởng.`);
                    window.close();
                });
            } else {
                alert(`${hostname} đã có trong danh sách tin tưởng.`);
            }
        });
    });

    blacklistBtn.addEventListener('click', async () => {
        if (!tab) return;
        const hostname = new URL(tab.url).hostname;
        chrome.storage.local.get(['blacklist'], (res) => {
            const list = res.blacklist || [];
            if (!list.includes(hostname)) {
                list.push(hostname);
                chrome.storage.local.set({ blacklist: list }, () => {
                    alert(`Đã chặn domain ${hostname}.`);
                    window.close();
                });
            } else {
                alert(`${hostname} đã có trong danh sách chặn.`);
            }
        });
    });

    // ── 3. Lịch sử quét ─────────────────────────────────────────────────────
    function loadHistory() {
        chrome.storage.local.get(['scanHistory'], (result) => {
            const history = result.scanHistory || [];
            if (history.length === 0) {
                historyList.innerHTML = '<div style="text-align:center; color:#64748b; padding:20px;">Trống</div>';
                return;
            }
            historyList.innerHTML = history.map(item => {
                const color = item.status_code === 'dangerous' ? 'var(--danger)' :
                              item.status_code === 'suspicious' ? 'var(--warning)' : 'var(--success)';
                return `
                <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid ${color}">
                    <div style="font-size:12px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.url}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span style="font-size:11px; color:${color}">${item.status}</span>
                        <span style="font-size:10px; color:#64748b;">${item.timestamp}</span>
                    </div>
                </div>`;
            }).join('');
        });
    }

    // ── Helper: Gửi báo cáo ẩn danh ─────────────────────────────────────────
    function sendReport(reportType, content, elementType = 'text') {
        fetch('http://localhost:5000/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_type: reportType,
                element_type: elementType,
                content: String(content).substring(0, 500),
                page_domain: 'popup_manual_check',
                timestamp: new Date().toISOString()
            })
        }).catch(() => {});
    }

    // ── Helper: Tạo toolbar báo cáo và inject vào container ──────────────────
    function buildReportToolbar(container, getContent, elementType = 'text') {
        // Xóa toolbar cũ nếu có
        container.innerHTML = '';

        const toolbar = document.createElement('div');
        toolbar.className = 'report-toolbar';

        const label = document.createElement('span');
        label.className = 'report-label';
        label.textContent = 'Kết quả sai?';

        const fpBtn = document.createElement('button');
        fpBtn.className = 'report-btn report-btn-fp';
        fpBtn.innerHTML = '✓ Báo cáo sai';
        fpBtn.title = 'Đây KHÔNG phải spam (False Positive)';

        const fnBtn = document.createElement('button');
        fnBtn.className = 'report-btn report-btn-fn';
        fnBtn.innerHTML = '⚑ Bỏ sót';
        fnBtn.title = 'Có nội dung lừa đảo bị bỏ qua (False Negative)';

        function markSent(type) {
            const color = type === 'false_positive' ? '#10b981' : '#f59e0b';
            toolbar.innerHTML = `<span class="report-sent-msg" style="color:${color}">✓ Đã gửi báo cáo. Cảm ơn!</span>`;
        }

        fpBtn.addEventListener('click', () => {
            sendReport('false_positive', getContent(), elementType);
            markSent('false_positive');
        });

        fnBtn.addEventListener('click', () => {
            sendReport('false_negative', getContent(), elementType);
            markSent('false_negative');
        });

        toolbar.appendChild(label);
        toolbar.appendChild(fpBtn);
        toolbar.appendChild(fnBtn);
        container.appendChild(toolbar);
    }

    // ── 4. Kiểm tra văn bản thủ công ─────────────────────────────────────────
    let lastCheckedText = '';

    checkBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;
        lastCheckedText = text;

        checkBtn.textContent = 'Đang phân tích...';
        checkBtn.disabled = true;
        manualReportArea.innerHTML = ''; // Xóa báo cáo cũ

        fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            manualResult.style.display = 'block';

            if (data.is_spam) {
                manualStatusText.innerHTML =
                    `<span style="color:var(--danger)">🚨 Cảnh báo:</span> Đây là tin nhắn <b>lừa đảo/spam</b> (${data.probability}%)`;
            } else {
                manualStatusText.innerHTML =
                    `<span style="color:var(--success)">✅ An toàn:</span> Không phát hiện yếu tố spam (${data.probability}%)`;
            }

            // Thêm toolbar báo cáo
            buildReportToolbar(manualReportArea, () => lastCheckedText, 'text');
        })
        .catch(() => {
            manualResult.style.display = 'block';
            manualStatusText.innerHTML = `<span style="color:var(--danger)">❌ Lỗi:</span> Không kết nối được API. Hãy chắc API đang chạy!`;
        })
        .finally(() => {
            checkBtn.textContent = '🔍 Phân tích bằng AI';
            checkBtn.disabled = false;
        });
    });

    // ── 5. Computer Vision - Quét Toàn Màn Hình ──────────────────────────────
    let lastCvMessage = '';

    scanScreenBtn.addEventListener('click', async () => {
        scanScreenBtn.disabled = true;
        const originalHTML = scanScreenBtn.innerHTML;
        scanScreenBtn.innerHTML = '<span style="font-size:20px">⏳</span><span>Đang chụp ảnh / Phân tích OCR...</span>';

        cvResult.style.display = 'block';
        cvStatusText.innerHTML = 'Đang chụp hình và khởi chạy AI...';
        cvContentText.style.display = 'none';
        cvReportArea.innerHTML = '';

        try {
            const dataUrl = await new Promise((resolve, reject) => {
                chrome.tabs.captureVisibleTab(null, { format: 'png', quality: 100 }, (url) => {
                    if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
                    else resolve(url);
                });
            });

            const response = await fetch('http://localhost:5000/predict_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_url: dataUrl })
            });
            const data = await response.json();
            lastCvMessage = data.message || '';

            if (data.is_spam) {
                cvStatusText.innerHTML = `<span style="color:var(--danger)">🚨 Cảnh báo Lừa đảo / Spam:</span> Tỷ lệ rủi ro <b>${data.probability}%</b>`;
                buildReportToolbar(cvReportArea, () => lastCvMessage, 'image');
            } else if (data.message === '[Không tìm thấy chữ trong ảnh]') {
                cvStatusText.innerHTML = `<span style="color:var(--warning)">⚠️ Không nhận diện được chữ trong khung hình.</span>`;
            } else {
                cvStatusText.innerHTML = `<span style="color:var(--success)">✅ An toàn:</span> Hình ảnh không chứa yếu tố độc hại (${data.probability}%)`;
                buildReportToolbar(cvReportArea, () => lastCvMessage, 'image');
            }

            if (data.message && data.message !== '[Không tìm thấy chữ trong ảnh]') {
                cvContentText.style.display = 'block';
                cvContentText.innerText = `Nội dung OCR: ${data.message}`;
            }

        } catch (error) {
            console.error(error);
            cvStatusText.innerHTML = `<span style="color:var(--danger)">❌ Lỗi:</span> Không thể chụp ảnh hoặc API chưa chạy!`;
        } finally {
            scanScreenBtn.disabled = false;
            scanScreenBtn.innerHTML = originalHTML;
        }
    });
});

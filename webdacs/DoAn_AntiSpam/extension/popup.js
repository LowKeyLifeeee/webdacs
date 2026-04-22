document.addEventListener('DOMContentLoaded', async () => {
    // Elements
    const homeTab = document.getElementById('homeTab');
    const historyTab = document.getElementById('historyTab');
    const homeView = document.getElementById('homeView');
    const historyView = document.getElementById('historyView');
    const historyList = document.getElementById('historyList');

    const siteStatusCard = document.getElementById('siteStatusCard');
    const siteIcon = document.getElementById('siteIcon');
    const siteStatusText = document.getElementById('siteStatusText');
    const siteStatusDesc = document.getElementById('siteStatusDesc');
    const analysisDetails = document.getElementById('analysisDetails');
    const reasonsList = document.getElementById('reasonsList');
    const whitelistBtn = document.getElementById('whitelistBtn');
    const blacklistBtn = document.getElementById('blacklistBtn');

    const textInput = document.getElementById('textInput');
    const checkBtn = document.getElementById('checkBtn');
    const manualResult = document.getElementById('manualResult');
    const manualStatusText = document.getElementById('manualStatusText');

    const scanScreenBtn = document.getElementById('scanScreenBtn');
    const cvResult = document.getElementById('cvResult');
    const cvStatusText = document.getElementById('cvStatusText');
    const cvContentText = document.getElementById('cvContentText');

    // --- Tab Switching Logic ---
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

    // 1. Phân tích Tab hiện tại
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
        chrome.storage.local.get([`analysis_${tab.id}`], (result) => {
            const data = result[`analysis_${tab.id}`];
            if (data) {
                updateSiteUI(data);
            } else {
                siteStatusText.innerText = "Chưa có dữ liệu";
                siteStatusDesc.innerText = "Hãy load lại trang hoặc đợi phân tích";
            }
        });
    }

    function updateSiteUI(data) {
        siteStatusCard.classList.remove('status-safe', 'status-warning', 'status-dangerous');
        
        if (data.status_code === 'dangerous') {
            siteStatusCard.classList.add('status-dangerous');
            siteIcon.innerText = "🚫";
            siteStatusText.innerText = "NGUY HIỂM";
            siteStatusDesc.innerText = "Trang web này có dấu hiệu lừa đảo cao!";
        } else if (data.status_code === 'suspicious') {
            siteStatusCard.classList.add('status-warning');
            siteIcon.innerText = "⚠️";
            siteStatusText.innerText = "NGHI NGỜ";
            siteStatusDesc.innerText = "Hãy cẩn thận khi nhập thông tin tại đây.";
        } else {
            siteStatusCard.classList.add('status-safe');
            siteIcon.innerText = "✅";
            siteStatusText.innerText = "AN TOÀN";
            siteStatusDesc.innerText = "Không phát hiện dấu hiệu bất thường.";
        }

        if (data.reasons && data.reasons.length > 0) {
            analysisDetails.style.display = 'block';
            reasonsList.innerHTML = data.reasons.map(r => `<div class="reason-item">${r}</div>`).join('');
        }
    }

    // 2. Xử lý Whitelist / Blacklist
    whitelistBtn.addEventListener('click', async () => {
        const hostname = new URL(tab.url).hostname;
        chrome.storage.local.get(['whitelist'], (res) => {
            const list = res.whitelist || [];
            if (!list.includes(hostname)) {
                list.push(hostname);
                chrome.storage.local.set({ whitelist: list }, () => {
                    alert(`Đã thêm ${hostname} vào danh sách tin tưởng.`);
                    window.close(); // Đóng popup để refresh
                });
            }
        });
    });

    blacklistBtn.addEventListener('click', async () => {
        const hostname = new URL(tab.url).hostname;
        chrome.storage.local.get(['blacklist'], (res) => {
            const list = res.blacklist || [];
            if (!list.includes(hostname)) {
                list.push(hostname);
                chrome.storage.local.set({ blacklist: list }, () => {
                    alert(`Đã chặn domain ${hostname}.`);
                    window.close();
                });
            }
        });
    });

    // 3. Tải lịch sử quét
    function loadHistory() {
        chrome.storage.local.get(['scanHistory'], (result) => {
            const history = result.scanHistory || [];
            if (history.length === 0) {
                historyList.innerHTML = '<div style="text-align:center; color:#64748b; padding:20px;">Trống</div>';
                return;
            }

            historyList.innerHTML = history.map(item => `
                <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid ${item.status_code === 'dangerous' ? 'var(--danger)' : (item.status_code === 'suspicious' ? 'var(--warning)' : 'var(--success)')}">
                    <div style="font-size:12px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.url}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span style="font-size:11px; color:${item.status_code === 'dangerous' ? 'var(--danger)' : (item.status_code === 'suspicious' ? 'var(--warning)' : 'var(--success)')}">${item.status}</span>
                        <span style="font-size:10px; color:#64748b;">${item.timestamp}</span>
                    </div>
                </div>
            `).join('');
        });
    }

    // 3. Kiểm tra văn bản thủ công
    checkBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;

        checkBtn.innerText = "Đang phân tích...";
        checkBtn.disabled = true;

        fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            manualResult.style.display = 'block';
            manualStatusText.innerHTML = data.is_spam 
                ? `<span style="color:var(--danger)">🚨 Cảnh báo:</span> Đây là tin nhắn lừa đảo (${data.probability}%)`
                : `<span style="color:var(--success)">✅ An toàn:</span> Không phát hiện yếu tố spam.`;
        })
        .catch(() => manualStatusText.innerText = "Lỗi kết nối!")
        .finally(() => {
            checkBtn.innerText = "Phân tích bằng AI";
            checkBtn.disabled = false;
        });
    });

    // 4. Computer Vision - Quét Toàn Màn Hình
    scanScreenBtn.addEventListener('click', async () => {
        scanScreenBtn.disabled = true;
        const originalText = scanScreenBtn.innerHTML;
        scanScreenBtn.innerHTML = '<span style="font-size: 20px;">⏳</span><span>Đang chụp ảnh/Phân tích OCR...</span>';
        
        cvResult.style.display = 'block';
        cvStatusText.innerHTML = "Đang chụp hình và khởi chạy AI...";
        cvContentText.style.display = 'none';

        try {
            // Chụp khung nhìn hiện tại
            const dataUrl = await new Promise((resolve, reject) => {
                chrome.tabs.captureVisibleTab(null, {format: 'png', quality: 100}, (url) => {
                    if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
                    else resolve(url);
                });
            });

            // Gửi dữ liệu ảnh lên API local
            const response = await fetch('http://localhost:5000/predict_image', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ image_url: dataUrl }) 
            });
            const data = await response.json();

            if (data.is_spam) {
                cvStatusText.innerHTML = `<span style="color:var(--danger)">🚨 Cảnh báo Lừa đảo / Spam:</span> Tỷ lệ rủi ro (${data.probability}%)`;
            } else if (data.message === '[Không tìm thấy chữ trong ảnh]') {
                cvStatusText.innerHTML = `<span style="color:var(--warning)">⚠️ Cảnh báo:</span> Không thể nhận diện được chữ trong khung hình.`;
            } else {
                cvStatusText.innerHTML = `<span style="color:var(--success)">✅ An toàn:</span> Hình ảnh không chứa yếu tố độc hại (${data.probability}%)`;
            }
            
            if (data.message && data.message !== '[Không tìm thấy chữ trong ảnh]') {
                cvContentText.style.display = 'block';
                cvContentText.innerText = `Nội dung: ${data.message}`;
            }

        } catch (error) {
            console.error(error);
            cvStatusText.innerHTML = `<span style="color:var(--danger)">❌ Lỗi:</span> Không thể chụp ảnh hoặc API chưa chạy. Khởi động lại api.py và cấp quyền Extension!`;
        } finally {
            scanScreenBtn.disabled = false;
            scanScreenBtn.innerHTML = originalText;
        }
    });
});

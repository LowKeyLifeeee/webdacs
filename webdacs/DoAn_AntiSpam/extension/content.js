// ═══════════════════════════════════════════════════════════════════════════
// Anti-Spam Pro - Content Script v3.0
// Tự động quét và cảnh báo ảnh / link / text lừa đảo trên trang web
// ═══════════════════════════════════════════════════════════════════════════
console.log('🛡️ Anti-Spam Pro v3.0 Content Script active on:', window.location.hostname);

const API_BASE = 'http://localhost:5000';

// ── Kiểm tra kết nối API ngay khi script khởi động ──────────────────────
fetch(`${API_BASE}/ping`)
    .then(r => r.json())
    .then(d => console.log('%c✅ AntiSpam API online', 'color:green;font-weight:bold', d))
    .catch(() => console.warn('%c⚠️ AntiSpam: API offline - keyword detection vẫn chạy', 'color:orange;font-weight:bold'));

// ─── Danh sách từ khóa ────────────────────────────────────────────────────
const PHISHING_KEYWORDS = [
    'đăng nhập', 'login', 'verify', 'xác thực', 'mật khẩu',
    'urgent', 'khẩn cấp', 'tài khoản bị khóa', 'nạp tiền',
    'trúng thưởng', 'nhận quà', 'tri ân',
    'casino', 'cá cược', 'đánh bài', 'tài xỉu', 'xóc đĩa', 'lô đề', 'xổ số',
    'jackpot', 'slot', 'baccarat', 'poker', 'nhà cái', 'kèo', 'cược',
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'hobet', 'kclub', 'fb88',
    'v9bet', 'w88', 'bet88', 'new88', '789bet', '8xbet', 'go88', 'kubet',
    'jun88', 'sunwin', 'iwin', 'hitclub', 'b52', 'okvip', 'cf68', 'debet',
    'siêu hũ', 'hũ bạc tỷ', 'nạp lần đầu', 'tặng nạp', 'x2 tiền', 'x3 tiền',
    'hoàn trả', 'rút tiền', 'nhận ngay', 'cổng game', 'xanh chín',
    'live casino', 'dealer', 'sign up bonus', 'welcome bonus'
];

const GAMBLING_IMG_KEYWORDS = [
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'hobet', 'kclub', 'fb88', 'f8bet',
    'v9bet', 'w88', 'bet88', 'new88', '789bet', '8xbet', 'go88', 'kubet',
    'jun88', 'sunwin', 'iwin', 'hitclub', 'b52', 'okvip', 'cf68', 'debet',
    '79king', '7ball', 'casino', 'gamble', 'gambling', 'poker', 'jackpot',
    'lottery', 'lotto', 'betwin', 'winbet', 'slot', 'wager', 'livecasino',
    'sportsbet', 'ad_banner', 'quảng cáo', 'banner_ads', 'promo'
];

const GAMBLING_URL_KEYWORDS = [
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'hobet', 'kclub', 'v9bet',
    'w88', 'new88', '789bet', '8xbet', 'go88', 'kubet', 'jun88', 'sunwin',
    'iwin', 'hitclub', 'b52', 'okvip', 'cf68', 'debet', 'jackpot', 'casino',
    'gamble', 'gambling', 'poker', 'lottery', 'lotto', 'betwin', 'wager',
    'livecasino', 'sportsbet', 'slot', 'bet88'
];

// ─── Inject CSS ────────────────────────────────────────────────────────────
const style = document.createElement('style');
style.id = 'antispam-styles';
style.textContent = `
  .antispam-wrapper {
    position: relative !important;
    display: inline-block !important;
  }
  .antispam-highlighted {
    position: relative !important;
    border: 3px solid #ef4444 !important;
    border-radius: 6px !important;
    background-color: rgba(239, 68, 68, 0.1) !important;
    box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2) !important;
  }
  .antispam-highlighted-link {
    outline: 3px dashed #f59e0b !important;
    outline-offset: 2px !important;
    background-color: rgba(245, 158, 11, 0.15) !important;
    border-radius: 3px !important;
  }
  .antispam-highlighted-img {
    outline: 4px solid #ef4444 !important;
    outline-offset: 4px !important;
    filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.8)) !important;
    border-radius: 4px !important;
  }
  .antispam-badge {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 2147483647 !important;
    background: linear-gradient(135deg, #dc2626, #991b1b) !important;
    color: white !important;
    font-size: 11px !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
    font-weight: 700 !important;
    padding: 3px 8px !important;
    border-radius: 0 0 8px 0 !important;
    white-space: nowrap !important;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.4) !important;
    pointer-events: none !important;
    letter-spacing: 0.3px !important;
    animation: antispam-pop 0.3s cubic-bezier(0.175,0.885,0.32,1.275) !important;
    max-width: 300px !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }
  .antispam-badge-link {
    background: linear-gradient(135deg, #d97706, #92400e) !important;
    box-shadow: 2px 2px 8px rgba(217,119,6,0.5) !important;
  }
  .antispam-report-bar {
    position: absolute !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 2147483647 !important;
    display: flex !important;
    gap: 4px !important;
    padding: 3px !important;
    background: rgba(0,0,0,0.6) !important;
    backdrop-filter: blur(4px) !important;
    justify-content: flex-end !important;
    animation: antispam-pop 0.3s ease !important;
  }
  .antispam-rbtn {
    font-size: 9px !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
    font-weight: 700 !important;
    padding: 2px 7px !important;
    border-radius: 8px !important;
    border: none !important;
    cursor: pointer !important;
    pointer-events: all !important;
    line-height: 1.5 !important;
    white-space: nowrap !important;
  }
  .antispam-rbtn-fp { background: #10b981 !important; color: white !important; }
  .antispam-rbtn-fn { background: #f59e0b !important; color: white !important; }
  .antispam-rbtn:hover { opacity: 0.8 !important; }
  .antispam-rbtn.sent { background: #475569 !important; cursor: default !important; pointer-events: none !important; }

  /* Toast thông báo nổi */
  #antispam-toast-container {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    z-index: 2147483647 !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    pointer-events: none !important;
  }
  .antispam-toast {
    background: linear-gradient(135deg, #1e1b4b, #312e81) !important;
    border: 1px solid rgba(239,68,68,0.5) !important;
    border-left: 4px solid #ef4444 !important;
    color: white !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    max-width: 320px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    animation: antispam-slideIn 0.4s cubic-bezier(0.175,0.885,0.32,1.275) !important;
    pointer-events: all !important;
    cursor: default !important;
    line-height: 1.5 !important;
  }
  .antispam-toast.warn {
    border-left-color: #f59e0b !important;
    border-color: rgba(245,158,11,0.5) !important;
  }
  .antispam-toast-title {
    font-weight: 700 !important;
    font-size: 13px !important;
    margin-bottom: 2px !important;
    display: block !important;
  }
  .antispam-toast-body {
    color: rgba(255,255,255,0.8) !important;
    font-size: 11px !important;
    display: block !important;
    word-break: break-all !important;
  }
  @keyframes antispam-pop {
    from { opacity: 0; transform: scale(0.8); }
    to   { opacity: 1; transform: scale(1); }
  }
  @keyframes antispam-slideIn {
    from { opacity: 0; transform: translateX(40px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  @keyframes antispam-slideOut {
    from { opacity: 1; transform: translateX(0); }
    to   { opacity: 0; transform: translateX(40px); }
  }
`;
if (!document.getElementById('antispam-styles')) {
    document.head.appendChild(style);
}

// ─── Toast Notification ────────────────────────────────────────────────────
let toastContainer = null;
let toastCount = 0;

function showToast(title, body, type = 'danger') {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'antispam-toast-container';
        document.body.appendChild(toastContainer);
    }

    toastCount++;
    if (toastCount > 5) return; // Không spam quá nhiều toast

    const toast = document.createElement('div');
    toast.className = `antispam-toast${type === 'warn' ? ' warn' : ''}`;
    toast.innerHTML = `
        <span class="antispam-toast-title">🚨 ${title}</span>
        <span class="antispam-toast-body">${body.substring(0, 100)}</span>
    `;
    toastContainer.appendChild(toast);

    // Tự xóa sau 5 giây
    setTimeout(() => {
        toast.style.animation = 'antispam-slideOut 0.3s ease forwards';
        setTimeout(() => {
            toast.remove();
            toastCount = Math.max(0, toastCount - 1);
        }, 300);
    }, 5000);
}

// ─── Bóc tách token từ URL (path + filename + query) ─────────────────────
function extractUrlTokens(rawUrl) {
    try {
        const u = new URL(rawUrl);
        const tokens = [];
        const pathParts = u.pathname.split('/').filter(Boolean);

        for (const part of pathParts) {
            const lower = part.toLowerCase();
            tokens.push(lower);
            const noExt = lower.replace(/\.[^.]+$/, '');     // bỏ extension
            if (noExt !== lower) tokens.push(noExt);
            noExt.split(/[-_.]+/).forEach(t => t.length > 1 && tokens.push(t));
        }

        u.searchParams.forEach((v, k) => {
            tokens.push(k.toLowerCase());
            tokens.push(v.toLowerCase());
        });

        return tokens.join(' ');
    } catch {
        return rawUrl.toLowerCase();
    }
}

// ─── Gửi báo cáo ──────────────────────────────────────────────────────────
function sendReport(reportType, content, elementType) {
    fetch(`${API_BASE}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            report_type: reportType,
            element_type: elementType,
            content: String(content).substring(0, 500),
            page_domain: window.location.hostname,
            timestamp: new Date().toISOString()
        })
    }).catch(() => { });
}

// ─── Tạo report buttons ────────────────────────────────────────────────────
function createReportBar(originalText, elementType) {
    const bar = document.createElement('div');
    bar.className = 'antispam-report-bar';

    const fp = document.createElement('button');
    fp.className = 'antispam-rbtn antispam-rbtn-fp';
    fp.textContent = '✓ Báo cáo sai';
    fp.addEventListener('click', e => {
        e.stopPropagation(); e.preventDefault();
        sendReport('false_positive', originalText, elementType);
        fp.textContent = '✓ Đã gửi'; fp.classList.add('sent');
        fn.classList.add('sent');
    });

    const fn = document.createElement('button');
    fn.className = 'antispam-rbtn antispam-rbtn-fn';
    fn.textContent = '⚑ Bỏ sót';
    fn.addEventListener('click', e => {
        e.stopPropagation(); e.preventDefault();
        sendReport('false_negative', originalText, elementType);
        fn.textContent = '✓ Đã gửi'; fn.classList.add('sent');
        fp.classList.add('sent');
    });

    bar.appendChild(fp);
    bar.appendChild(fn);
    return bar;
}

// ─── Highlight ảnh ────────────────────────────────────────────────────────
function highlightImage(imgEl, reason) {
    if (imgEl.dataset.antispamDone) return;
    imgEl.dataset.antispamDone = 'true';

    console.warn(`[AntiSpam] 🚨 Ảnh bị chặn: ${reason} | src: ${(imgEl.src || '').substring(0, 80)}`);

    try {
        // Tạo wrapper bao quanh ảnh
        const wrapper = document.createElement('span');
        wrapper.className = 'antispam-wrapper';

        const parent = imgEl.parentNode;
        if (!parent) {
            // Không có parent - chỉ thêm outline
            imgEl.classList.add('antispam-highlighted-img');
            return;
        }

        parent.insertBefore(wrapper, imgEl);
        wrapper.appendChild(imgEl);

        imgEl.classList.add('antispam-highlighted-img');

        // Badge ở góc trên
        const badge = document.createElement('span');
        badge.className = 'antispam-badge';
        badge.textContent = `🚨 Cờ bạc/Lừa đảo`;
        badge.title = reason;
        wrapper.appendChild(badge);

        // Report bar ở dưới
        wrapper.appendChild(createReportBar(reason, 'image'));

        // Toast thông báo
        showToast('Phát hiện quảng cáo cờ bạc!', reason);

    } catch (err) {
        // Fallback: chỉ outline
        console.warn('[AntiSpam] Lỗi wrapper:', err.message);
        imgEl.classList.add('antispam-highlighted-img');
    }
}

// ─── Highlight text/link ───────────────────────────────────────────────────
function highlightElement(el, reason, type = 'text') {
    if (el.dataset.antispamDone) return;
    el.dataset.antispamDone = 'true';

    console.warn(`[AntiSpam] 🚨 ${type} bị đánh dấu: ${reason.substring(0, 60)}`);

    if (type === 'link') {
        el.classList.add('antispam-highlighted-link');
    } else {
        el.classList.add('antispam-highlighted');
        el.style.position = el.style.position || 'relative';
    }

    // Badge
    const badge = document.createElement('span');
    badge.className = `antispam-badge${type === 'link' ? ' antispam-badge-link' : ''}`;
    badge.style.cssText = 'position:absolute;top:-16px;left:0;';
    badge.textContent = type === 'link' ? '⚠️ Link nghi ngờ' : '🚨 Spam';
    badge.title = reason;

    // Report buttons
    const reportBar = createReportBar(reason, type);
    reportBar.style.cssText = 'position:absolute;top:-16px;right:0;display:flex;gap:4px;';

    el.appendChild(badge);
    el.appendChild(reportBar);

    if (type !== 'link') {
        showToast('Phát hiện nội dung spam!', reason, 'warn');
    }
}

// ─── Phát hiện ảnh qua keyword trong URL/alt/href ─────────────────────────
function quickDetectImage(imgEl) {
    const rawSrc = imgEl.src || imgEl.currentSrc
        || imgEl.getAttribute('data-src')      // lazy load
        || imgEl.getAttribute('data-lazy-src') // lazy load variant
        || '';
    const src = rawSrc.toLowerCase();
    const alt = (imgEl.alt || '').toLowerCase();
    const title = (imgEl.title || '').toLowerCase();
    const srcTokens = extractUrlTokens(rawSrc);
    const combined = `${src} ${alt} ${title} ${srcTokens}`;

    // Kiểm tra keyword trong src/alt/title/tokens
    const hit = GAMBLING_IMG_KEYWORDS.find(k => combined.includes(k));
    if (hit) {
        return {
            hit: true,
            reason: `Ảnh cờ bạc (keyword "${hit}" trong ${src.includes(hit) ? 'URL ảnh' : 'alt/title'})`
        };
    }

    // Kiểm tra link cha <a href>
    const parentLink = imgEl.closest('a[href]');
    if (parentLink) {
        const rawHref = parentLink.href || '';
        const hrefTokens = extractUrlTokens(rawHref);
        const hrefAll = `${rawHref.toLowerCase()} ${hrefTokens}`;
        const hrefHit = GAMBLING_URL_KEYWORDS.find(k => hrefAll.includes(k));
        if (hrefHit) {
            return {
                hit: true,
                reason: `Ảnh dẫn đến trang cờ bạc (keyword "${hrefHit}" trong link)`
            };
        }
    }

    return { hit: false };
}

// ─── Xử lý một ảnh ────────────────────────────────────────────────────────
function processImage(imgEl) {
    const src = imgEl.src || imgEl.currentSrc
        || imgEl.getAttribute('data-src')
        || imgEl.getAttribute('data-lazy-src');

    if (!src || imgEl.dataset.antispamDone) return;
    if (src.startsWith('data:image')) return;

    // Tầng 1: keyword nhanh (không cần API)
    const quick = quickDetectImage(imgEl);
    if (quick.hit) {
        highlightImage(imgEl, quick.reason);
        return;
    }

    // Tầng 2: OCR (chỉ khi ảnh đủ lớn và đã load)
    const tryOCR = () => {
        const w = imgEl.naturalWidth || imgEl.width || 0;
        const h = imgEl.naturalHeight || imgEl.height || 0;
        if (w >= 150 && h >= 60 && !imgEl.dataset.antispamDone) {
            runOCR(imgEl, src);
        }
    };

    if (imgEl.complete && imgEl.naturalWidth > 0) {
        tryOCR();
    } else {
        imgEl.addEventListener('load', tryOCR, { once: true });
    }
}

async function runOCR(imgEl, src) {
    try {
        const resp = await fetch(src, { mode: 'cors' });
        if (!resp.ok) return;
        const blob = await resp.blob();
        const base64 = await new Promise(resolve => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });

        const res = await fetch(`${API_BASE}/predict_image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_url: base64 })
        });
        const data = await res.json();

        if (data.is_spam && !imgEl.dataset.antispamDone) {
            console.warn(`[AntiSpam] OCR spam: ${data.message}`);
            highlightImage(imgEl, `OCR phát hiện: ${data.message}`);
        }
    } catch (e) { /* CORS / network */ }
}

// ─── Quét text ────────────────────────────────────────────────────────────
async function checkText(el, text) {
    try {
        const res = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        if (data.is_spam) highlightElement(el, text.substring(0, 60), 'text');
    } catch { /* API offline */ }
}

// ─── Quét link ────────────────────────────────────────────────────────────
async function checkLink(linkEl) {
    const url = linkEl.href;
    if (!url || linkEl.dataset.antispamDone) return;

    // Kiểm tra nhanh bằng keyword trước (không gọi API)
    const tokens = `${url.toLowerCase()} ${extractUrlTokens(url)}`;
    const hit = GAMBLING_URL_KEYWORDS.find(k => tokens.includes(k));
    if (hit) {
        highlightElement(linkEl, `Link cờ bạc: "${hit}"`, 'link');
        return;
    }

    // Gọi API kiểm tra sâu hơn
    try {
        const res = await fetch(`${API_BASE}/predict-url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await res.json();
        if (data.status_code === 'dangerous' || data.status_code === 'suspicious') {
            highlightElement(linkEl, (data.reasons || [url])[0], 'link');
        }
    } catch { /* API offline */ }
}

// ─── Hàm quét chính ───────────────────────────────────────────────────────
async function scanPage() {
    console.log('[AntiSpam] Bắt đầu quét trang:', window.location.href);
    toastCount = 0; // Reset đếm toast mỗi lần quét

    // 1. Quét TẤT CẢ ảnh (kể cả lazy-load)
    const imgs = document.querySelectorAll('img, [data-src], [data-lazy-src]');
    console.log(`[AntiSpam] Tìm thấy ${imgs.length} ảnh để kiểm tra`);
    for (const img of imgs) {
        await new Promise(r => setTimeout(r, 10)); // tránh block UI
        processImage(img);
    }

    // 2. Quét link external
    const links = document.querySelectorAll('a[href^="http"]');
    const topLinks = Array.from(links).slice(0, 50);
    console.log(`[AntiSpam] Kiểm tra ${topLinks.length} links`);
    for (const link of topLinks) {
        await new Promise(r => setTimeout(r, 30));
        checkLink(link);
    }

    // 3. Quét text
    const textEls = document.querySelectorAll('p, span, div, li, td');
    for (const el of textEls) {
        if (el.children.length === 0) {
            const text = (el.innerText || el.textContent || '').trim();
            if (text.length > 30 && text.length < 1000) {
                const hit = PHISHING_KEYWORDS.some(w => text.toLowerCase().includes(w));
                if (hit) checkText(el, text);
            }
        }
    }

    console.log('[AntiSpam] ✅ Hoàn thành quét trang');
}

// ─── Chạy khi trang tải ───────────────────────────────────────────────────
if (document.readyState === 'complete') {
    scanPage();
} else {
    window.addEventListener('load', scanPage);
}

// ─── MutationObserver cho SPA (Facebook, Zalo...) ────────────────────────
let debounce = null;
let pendingNodes = []; // Mảng chứa các node chờ xử lý

new MutationObserver((mutations) => {
    // 1. Gom tất cả các node mới vào mảng chờ
    mutations.forEach(m => {
        m.addedNodes.forEach(node => {
            if (node.nodeType === 1) pendingNodes.push(node);
        });
    });

    if (pendingNodes.length === 0) return;

    // 2. Chạy debounce
    clearTimeout(debounce);
    debounce = setTimeout(() => {
        // Lấy danh sách cần xử lý và làm rỗng mảng chờ cho lần sau
        const nodesToProcess = [...pendingNodes];
        pendingNodes = [];

        nodesToProcess.forEach(node => {
            const imgs = node.tagName === 'IMG' ? [node] :
                Array.from(node.querySelectorAll('img, [data-src]'));
            imgs.forEach(img => processImage(img));
        });
    }, 800);
}).observe(document.body, { childList: true, subtree: true });

// ─── Nhận lệnh từ background ──────────────────────────────────────────────
try {
    chrome.runtime.onMessage.addListener((request) => {
        if (request.action === 'HIGHLIGHT_ELEMENT') {
            try {
                const el = document.querySelector(request.selector);
                if (el) highlightElement(el, request.text || request.selector, request.type || 'text');
            } catch (e) { }
        }
    });
} catch (e) { /* Extension context invalid */ }

// ─── Auto scan màn hình (gửi về background) ───────────────────────────────
// Bọc trong try-catch để tránh lỗi "Extension context invalidated"
// khi extension được reload trong khi trang vẫn đang mở
function safeSendMessage(msg) {
    try {
        if (chrome && chrome.runtime && chrome.runtime.id) {
            chrome.runtime.sendMessage(msg).catch(() => { });
        }
    } catch (e) {
        // Extension context không còn hợp lệ → dừng interval
        clearInterval(autoScanInterval);
    }
}

const autoScanInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
        safeSendMessage({ action: 'REQUEST_AUTO_SCAN' });
    }
}, 2000);


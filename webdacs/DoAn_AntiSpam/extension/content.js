// Content script - Tự động quét trang web và phát hiện Phishing
console.log("🛡️ Anti-Spam (Pro) Content Script is active.");

const PHISHING_KEYWORDS = [
    'đăng nhập', 'login', 'verify', 'xác thực', 'mật khẩu', 
    'urgent', 'khẩn cấp', 'tài khoản bị khóa', 'nạp tiền',
    'trúng thưởng', 'nhận quà', 'tri ân'
];

async function scanForPhishing() {
    const pageText = document.body.innerText.toLowerCase();
    const hasSensitiveForm = document.querySelector('input[type="password"]') !== null;
    
    // 1. Kiểm tra từ khóa nhạy cảm trên trang
    let foundKeywords = PHISHING_KEYWORDS.filter(word => pageText.includes(word));
    
    if (foundKeywords.length > 2 || (hasSensitiveForm && foundKeywords.length > 0)) {
        console.warn("🚨 Cảnh báo: Trang web chứa nhiều từ khóa nhạy cảm và form đăng nhập.");
        
        // Gửi alert hoặc thông báo nếu cần (tùy chọn)
        // Lưu ý: Việc highlight trực tiếp có thể gây khó chịu, nên ta chỉ log hoặc báo về background
    }

    // 2. Kiểm tra các thẻ chứa nội dung dài (như tin nhắn, bài viết)
    const elements = document.querySelectorAll('p, span, div');
    for (let el of elements) {
        if (el.children.length === 0 && el.innerText.trim().length > 30 && el.innerText.trim().length < 1000) {
            const text = el.innerText.trim();
            
            // Chỉ gửi lên server nếu chứa từ khóa nghi vấn để tiết kiệm tài nguyên
            if (PHISHING_KEYWORDS.some(word => text.toLowerCase().includes(word))) {
                checkAndHighlight(el, text);
            }
        }
    }
}

async function checkAndHighlight(el, text) {
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text })
        });
        const result = await response.json();
        
        if (result && result.is_spam) {
            el.style.border = "2px dashed #ef4444";
            el.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
            el.style.position = "relative";
            
            const warningBadge = document.createElement('span');
            warningBadge.innerText = "⚠️ Cảnh báo AI";
            warningBadge.style.cssText = "position:absolute; top:-10px; right:0; background:#ef4444; color:white; font-size:10px; padding:2px 5px; border-radius:4px; z-index:1000;";
            el.appendChild(warningBadge);
        }
    } catch (e) {
        // Im silent on error
    }
}

// Chạy khi trang ổn định
if (document.readyState === 'complete') {
    scanForPhishing();
} else {
    window.addEventListener('load', scanForPhishing);
}

// 3. Tự động yêu cầu background chụp màn hình mỗi 2 giây
setInterval(() => {
    // Chỉ yêu cầu chụp nếu trang này đang được người dùng mở xem (visible)
    if (document.visibilityState === 'visible') {
        chrome.runtime.sendMessage({ action: "REQUEST_AUTO_SCAN" });
    }
}, 2000);

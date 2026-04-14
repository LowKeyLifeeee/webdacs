// Content script - Tự động quét trang web
console.log("🛡️ Anti-Spam Content Script đã được tải.");

// Hàm gửi text về Backend để kiểm tra
async function checkSpam(text) {
    if (text.length < 10) return null; // Bỏ qua text quá ngắn
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text })
        });
        return await response.json();
    } catch (e) {
        return null;
    }
}

// Quét các thẻ văn bản trên trang
async function scanPage() {
    const elements = document.querySelectorAll('p, span, h1, h2, h3, div');
    
    for (let el of elements) {
        // Chỉ quét các thẻ có text trực tiếp và không quá dài
        if (el.children.length === 0 && el.innerText.trim().length > 20 && el.innerText.trim().length < 500) {
            const text = el.innerText.trim();
            const result = await checkSpam(text);
            
            if (result && result.is_spam) {
                console.warn("🚨 Phát hiện Spam:", text);
                el.style.border = "2px solid red";
                el.style.backgroundColor = "#fff0f0";
                el.title = `Cảnh báo: AI nhận diện đây là Spam (${result.probability}%)`;
            }
        }
    }
}

// Chạy quét sau khi trang load xong 2 giây (để chờ các script khác load nội dung)
setTimeout(scanPage, 2000);

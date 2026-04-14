document.getElementById('checkBtn').addEventListener('click', async () => {
    const text = document.getElementById('textInput').value;
    const resultDiv = document.getElementById('result');
    
    if (!text.trim()) {
        alert('Vui lòng nhập nội dung!');
        return;
    }

    resultDiv.style.display = 'block';
    resultDiv.textContent = 'Đang kiểm tra...';
    resultDiv.className = '';

    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        if (data.is_spam) {
            resultDiv.textContent = `🚨 CẢNH BÁO: SPAM (${data.probability}%)`;
            resultDiv.className = 'spam';
        } else {
            resultDiv.textContent = `✅ AN TOÀN (${data.probability}%)`;
            resultDiv.className = 'safe';
        }
    } catch (error) {
        resultDiv.textContent = '❌ Lỗi kết nối đến Backend: ' + error.message;
        resultDiv.className = 'spam';
    }
});

// Background Script - Xử lý Menu chuột phải
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "checkSpamImage",
        title: "Kiểm tra Spam từ ảnh này 🛡️",
        contexts: ["image"]
    });
    
    // Thêm Menu chuột phải khi bôi đen chữ hoặc click chuột phải vào Link
    chrome.contextMenus.create({
        id: "checkSpamTextOrLink",
        title: "Kiểm tra đoạn tin nhắn hoặc URL này 🛡️",
        contexts: ["selection", "link"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "checkSpamImage") {
        const imageUrl = info.srcUrl;
        
        // Thông báo cho người dùng là đang kiểm tra
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (url) => { alert("Đang kiểm tra ảnh: " + url + "\nVui lòng đợi kết quả..."); },
            args: [imageUrl]
        });

        // Gửi URL ảnh về Backend
        fetch('http://localhost:5000/predict_image', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ image_url: imageUrl })
        })
        .then(response => response.json())
        .then(data => {
            let message = "";
            if (data.is_spam) {
                message = `🚨 CẢNH BÁO SPAM!\nNội dung trích xuất: "${data.message}"\nĐộ tin cậy: ${data.probability}%`;
            } else if (data.error) {
                message = `❌ Lỗi: ${data.error}`;
            } else {
                message = `✅ AN TOÀN.\nNội dung ảnh: "${data.message}"`;
            }
            
            // Hiển thị kết quả bằng Alert trên trang
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (msg) => { alert(msg); },
                args: [message]
            });
        })
        .catch(err => {
            console.error(err);
        });
    } else if (info.menuItemId === "checkSpamTextOrLink") {
        const contentToCheck = info.selectionText || info.linkUrl;
        
        if (!contentToCheck) return;

        // Tạo thông báo đang xử lý
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
            title: '🔎 Đang kiểm tra nội dung...',
            message: 'Vui lòng đợi kết quả từ máy chủ...'
        });

        // Gửi nội dung về Backend (local api)
        fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: contentToCheck })
        })
        .then(response => response.json())
        .then(data => {
            let title = "";
            let message = "";
            
            if (data.is_spam) {
                title = "🚨 CẢNH BÁO LỪA ĐẢO (SPAM)";
                message = `Độ tin cậy: ${data.probability}%\nNội dung có chứa yếu tố nguy hiểm hoặc lừa đảo.`;
            } else if (data.error) {
                title = "❌ Lỗi hệ thống";
                message = data.error;
            } else {
                title = "✅ NỘI DUNG AN TOÀN";
                message = `Độ tin cậy: ${data.probability}%\nKhông tìm thấy yếu tố lừa đảo.`;
            }
            
            // Hiển thị thông báo kết quả
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                title: title,
                message: message,
                priority: 2
            });
        })
        .catch(err => {
            console.error(err);
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                title: "❌ Lỗi kết nối",
                message: "Không thể kết nối đến máy chủ API local (localhost:5000)!",
                priority: 2
            });
        });
    }
});

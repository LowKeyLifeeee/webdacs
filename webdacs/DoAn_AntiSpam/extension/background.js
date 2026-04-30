// Background Script - Xử lý Menu chuột phải
chrome.runtime.onInstalled.addListener(() => {
    // Xóa tất cả menu cũ trước khi tạo lại (tránh lỗi trùng ID khi reload)
    chrome.contextMenus.removeAll(() => {

        // ── Menu CHA: luôn xuất hiện cho mọi trường hợp ──────────────────
        chrome.contextMenus.create({
            id: "antispamParent",
            title: "🛡️ Anti-Spam Detector (Pro)",
            contexts: ["image", "selection", "link", "page"]
        });

        // ── Sub-menu 1: Kiểm tra ảnh (hiện khi click phải vào ảnh) ───────
        chrome.contextMenus.create({
            id: "checkSpamImage",
            parentId: "antispamParent",
            title: "📸 Kiểm tra Spam từ ảnh này",
            contexts: ["image", "page"]   // "page" = fallback khi không có gì khác
        });

        // ── Sub-menu 2: Kiểm tra text/URL (hiện khi bôi đen hoặc link) ───
        chrome.contextMenus.create({
            id: "checkSpamTextOrLink",
            parentId: "antispamParent",
            title: "💬 Kiểm tra đoạn tin nhắn hoặc URL",
            contexts: ["selection", "link", "page"]
        });

        // ── Sub-menu 3: Quét URL trang hiện tại ──────────────────────────
        chrome.contextMenus.create({
            id: "checkCurrentPage",
            parentId: "antispamParent",
            title: "🔗 Phân tích URL trang này",
            contexts: ["image", "selection", "link", "page"]
        });

        // ── Separator ─────────────────────────────────────────────────────
        chrome.contextMenus.create({
            id: "separator1",
            parentId: "antispamParent",
            type: "separator",
            contexts: ["image", "selection", "link", "page"]
        });

        // ── Sub-menu 4: Báo cáo trang lừa đảo ────────────────────────────
        chrome.contextMenus.create({
            id: "reportPage",
            parentId: "antispamParent",
            title: "🚨 Báo cáo trang này là lừa đảo",
            contexts: ["image", "selection", "link", "page"]
        });
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "checkSpamImage") {
        const imageUrl = info.srcUrl;
        
        // 1. Dùng Scripting để convert ảnh sang Base64 trực tiếp trên trang (Xử lý được lỗi blob:)
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: async (url) => {
                try {
                    const resp = await fetch(url);
                    const blob = await resp.blob();
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                } catch (e) {
                    return url; // Nếu lỗi thì trả về URL gốc
                }
            },
            args: [imageUrl]
        }).then(results => {
            const base64Data = results[0].result;

            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => { alert("Đang phân tích hình ảnh... Vui lòng đợi kết quả."); }
            });

            // 2. Gửi Base64 về Backend
            return fetch('http://localhost:5000/predict_image', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ image_url: base64Data })
            });
        })
        .then(response => response.json())
        .then(data => {
            let statusIcon = "🟢";
            let statusText = "[MÀU XANH - AN TOÀN]";
            
            if (data.is_spam) {
                statusIcon = "🔴";
                statusText = "[MÀU ĐỎ - NGUY HIỂM]";
            } else if (data.probability < 50) { // Nếu độ tin cậy thấp, báo màu vàng
                statusIcon = "🟡";
                statusText = "[MÀU VÀNG - NGHI NGỜ]";
            }

            let message = `${statusIcon} ${statusText}\n--------------------------------\n`;
            if (data.is_spam) {
                message += `CẢNH BÁO: PHÁT HIỆN LỪA ĐẢO!\nTỷ lệ: ${data.probability}%\nNội dung: "${data.message}"`;
            } else {
                message += `Đánh giá: AN TOÀN\nĐộ tin cậy: ${data.probability}%\nNội dung: "${data.message}"`;
            }
            
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
            let icon = "🟢"; // Icon mặc định
            
            if (data.is_spam) {
                title = "🔴 [MÀU ĐỎ] - CẢNH BÁO LỪA ĐẢO";
                message = `Độ tin cậy: ${data.probability}%\nNội dung có chứa yếu tố nguy hiểm hoặc lừa đảo.`;
            } else if (data.probability < 50) {
                title = "🟡 [MÀU VÀNG] - NGHI NGỜ";
                message = `Độ tin cậy: ${data.probability}%\nNội dung chưa được xác thực rõ ràng.`;
            } else {
                title = "🟢 [MÀU XANH] - AN TOÀN";
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

    } else if (info.menuItemId === "checkCurrentPage") {
        // ── Phân tích URL trang hiện tại ─────────────────────────────────
        const url = tab.url;
        if (!url || !url.startsWith('http')) return;

        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
            title: '🔎 Đang phân tích URL...',
            message: url.substring(0, 100)
        });

        fetch('http://localhost:5000/predict-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        })
        .then(r => r.json())
        .then(data => {
            const icon = data.status_code === 'dangerous' ? '🔴' :
                         data.status_code === 'suspicious' ? '🟡' : '🟢';
            const reasons = (data.reasons || []).slice(0, 3).join('\n• ') || 'Không có dấu hiệu bất thường';
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                title: `${icon} ${data.status} (Điểm: ${data.score}/100)`,
                message: `• ${reasons}`,
                priority: 2
            });
        })
        .catch(() => {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                title: '❌ Lỗi kết nối API',
                message: 'Hãy chắc chắn api.py đang chạy!',
                priority: 2
            });
        });

    } else if (info.menuItemId === "reportPage") {
        // ── Báo cáo trang lừa đảo ────────────────────────────────────────
        const url = tab.url;
        fetch('http://localhost:5000/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_type: 'false_negative',
                element_type: 'page',
                content: url,
                page_domain: new URL(url).hostname,
                timestamp: new Date().toISOString()
            })
        })
        .then(() => {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                title: '✅ Đã gửi báo cáo',
                message: `Cảm ơn! Trang ${new URL(url).hostname} đã được ghi nhận là lừa đảo.`,
                priority: 1
            });
        })
        .catch(() => {});
    }
});

// --- NEW: Real-time URL Scanning ---
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Chỉ kiểm tra khi URL đã hoàn tất tải
    if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('http')) {
        checkURLSafety(tab.url, tabId);
    }
});

function checkURLSafety(url, tabId) {
    const hostname = new URL(url).hostname;

    chrome.storage.local.get(['whitelist', 'blacklist'], (result) => {
        const whitelist = result.whitelist || [];
        const blacklist = result.blacklist || [];

        if (whitelist.includes(hostname)) {
            updateBadge(tabId, "OK", "#4CAF50");
            chrome.storage.local.set({ [`analysis_${tabId}`]: { status: "Tin tưởng", status_code: "safe", reasons: ["Domain nằm trong Whitelist cá nhân"] } });
            return;
        }

        if (blacklist.includes(hostname)) {
            updateBadge(tabId, "!", "#F44336");
            const data = { status: "Đã bị chặn", status_code: "dangerous", reasons: ["Domain nằm trong Blacklist cá nhân"] };
            chrome.storage.local.set({ [`analysis_${tabId}`]: data });
            showDangerNotification(data.reasons[0]);
            return;
        }

        // Nếu không nằm trong list, gọi API phân tích
        fetch('http://localhost:5000/predict-url', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            let badgeText = "";
            let badgeColor = "";
            
            if (data.status_code === "dangerous") {
                badgeText = "!";
                badgeColor = "#F44336";
                showDangerNotification(data.reasons[0]);
            } else if (data.status_code === "suspicious") {
                badgeText = "?";
                badgeColor = "#FF9800";
            } else {
                badgeText = "OK";
                badgeColor = "#4CAF50";
            }
            
            updateBadge(tabId, badgeText, badgeColor);
            chrome.storage.local.set({ [`analysis_${tabId}`]: data });
            saveToHistory(url, data);
        })
        .catch(err => console.error("API Error:", err));
    });
}

function updateBadge(tabId, text, color) {
    chrome.action.setBadgeText({ text: text, tabId: tabId });
    chrome.action.setBadgeBackgroundColor({ color: color, tabId: tabId });
}

function showDangerNotification(reason) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
        title: "🔴 CẢNH BÁO NGUY HIỂM",
        message: `Trang web này có dấu hiệu lừa đảo!\n${reason || ""}`,
        priority: 2
    });
}

function saveToHistory(url, data) {
    chrome.storage.local.get(['scanHistory'], (result) => {
        let history = result.scanHistory || [];
        const newItem = {
            url: url,
            status: data.status,
            status_code: data.status_code,
            timestamp: new Date().toLocaleString('vi-VN')
        };
        
        // Tránh trùng lặp URL liên tiếp
        if (history.length > 0 && history[0].url === url) return;

        history.unshift(newItem);
        if (history.length > 50) history.pop(); // Giới hạn 50 mục
        
        chrome.storage.local.set({ scanHistory: history });
    });
}

// --- NEW: Auto Screen Capture (CV) ---
let isAutoScanning = false;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "REQUEST_AUTO_SCAN") {
        if (isAutoScanning) return; // Nếu đang xử lý ảnh cũ thì bỏ qua nhịp này
        
        // Kiểm tra xem tab gửi request có phải là tab đang active không
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (!tabs || tabs.length === 0 || tabs[0].id !== sender.tab.id) return;
            
            isAutoScanning = true;
            
            // Tiến hành chụp màn hình tab hiện tại
            chrome.tabs.captureVisibleTab(sender.tab.windowId, {format: 'png', quality: 50}, (dataUrl) => {
                if (chrome.runtime.lastError || !dataUrl) {
                    console.error("Capture Error:", chrome.runtime.lastError);
                    isAutoScanning = false;
                    return;
                }
                
                // Gửi về backend API
                fetch('http://localhost:5000/predict_image', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ image_url: dataUrl })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.is_spam) {
                        chrome.notifications.create({
                            type: 'basic',
                            iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                            title: "🚨 BÁO ĐỘNG LỪA ĐẢO (CV Auto)",
                            message: `Hệ thống vừa nhận diện màn hình có rủi ro (${data.probability}%).\nNội dung: ${data.message}`,
                            priority: 2,
                            requireInteraction: true // Thông báo ở đỏ giữ lại cho đến khi user tắt
                        });
                    }
                })
                .catch(err => {
                    console.error("Auto Scan Error:", err); 
                })
                .finally(() => {
                    isAutoScanning = false; 
                });
            });
        });
    }
});

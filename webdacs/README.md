# 🛡️ Hệ Thống AI Nhận Diện Tin Nhắn Spam & Lừa Đảo (V2.0 Pro)

Chào mừng bạn đến với phiên bản nâng cấp của dự án Hệ Thống Phát Hiện Tin Nhắn Rác. Phiên bản này được tích hợp trí tuệ nhân tạo (AI), công nghệ OCR và hệ thống phân tích URL độc hại để bảo vệ người dùng toàn diện trên không gian mạng.

## ✨ Các Tính Năng Nổi Bật (Mới Cập Nhật)

1.  **Phát hiện URL & Phishing (Mới):** Tự động phân tích các liên kết (URL) để phát hiện trang web lừa đảo, giả mạo thương hiệu hoặc thiếu bảo mật.
2.  **Hệ thống Icon 3 Màu (Mới):** 
    *   🟢 **Xanh lá:** An toàn.
    *   🟡 **Vàng:** Nghi ngờ/Chưa xác thực.
    *   🔴 **Đỏ:** Nguy hiểm/Lừa đảo.
3.  **Quét Ảnh Thông Minh (OCR Pro):** Tối ưu hóa cho các đoạn chat (Zalo, Facebook) với khả năng phóng ảnh và khử nhiễu.
4.  **Cảnh báo Real-time:** Tự động thay đổi màu Icon trình duyệt (Badge) và gửi Notification khi bạn truy cập web.
5.  **Whitelist & Blacklist:** Cho phép người dùng tùy chỉnh danh sách domain tin tưởng hoặc chặn hoàn toàn.
6.  **Giao diện Premium:** Popup hiện đại sử dụng Glassmorphism cùng hệ thống "Explainable AI" giải thích lý do cảnh báo.

---

## ⚙️ Hướng Dẫn Cài Đặt

### 1. Yêu cầu hệ thống
- **Python:** 3.8 - 3.12+
- **Tesseract OCR:** Cần cài đặt phần mềm Tesseract OCR vào máy. (Mặc định trong code trỏ tới `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### 2. Cài đặt các thư viện cần thiết
Bạn cần mở Terminal tại thư mục `DoAn_AntiSpam` và chạy lệnh sau để cài đặt toàn bộ môi trường:

```cmd
pip install flask flask-cors streamlit joblib scikit-learn pillow pytesseract requests
```

### 3. Danh sách thư viện đã sử dụng
-   **Flask:** Xây dựng máy chủ mã nguồn (Backend API) cho Extension.
-   **Flask-CORS:** Hỗ trợ kết nối giữa Extension và máy chủ API.
-   **Streamlit:** Xây dựng giao diện Web Demo chuyên nghiệp.
-   **scikit-learn:** Thư viện AI chính để phân loại văn bản (LinearSVC, TF-IDF).
-   **Pillow (PIL):** Xử lý hình ảnh, tăng độ tương phản trước khi nhận diện chữ.
-   **pytesseract:** Cầu nối sử dụng công cụ Tesseract OCR để đọc chữ.
-   **Requests:** Tải dữ liệu ảnh từ các URL để phân tích.
-   **joblib:** Lưu trữ và tải các mô hình trí tuệ nhân tạo đã huấn luyện.

---

## 🚀 Hướng Dẫn Vận Hành

Dự án gồm 3 phần chính hoạt động song song:

### Bước 1: Khởi chạy Backend API (Bắt buộc cho Extension)
Backend này giúp xử lý các yêu cầu quét từ tiện ích mở rộng trên trình duyệt.
```cmd
cd DoAn_AntiSpam
python api.py
```

### Bước 2: Khởi chạy Giao diện Web (Streamlit UI)
Đây là bản demo web hoàn chỉnh để bạn upload ảnh hoặc dán nội dung thủ công.
```cmd
cd DoAn_AntiSpam
python -m streamlit run app.py
```

### Bước 3: Cài đặt tiện ích mở rộng (Chrome Extension)
1. Truy cập `chrome://extensions/` trên Chrome/Edge/Cốc Cốc.
2. Bật **Chế độ cho nhà phát triển (Developer mode)**.
3. Nhấp vào **Tải tiện ích đã giải nén (Load unpacked)**.
4. Chọn thư mục `extension` trong dự án của bạn.

---

## 🧠 Nguyên Lý Hoạt Động

Dựa trên công nghệ **Explainable AI (XAI)**, hệ thống không chỉ trả về kết quả mà còn đưa ra lý do:
- **HTTPS:** Kiểm tra chứng chỉ bảo mật.
- **Typosquatting:** Kiểm tra xem domain có đang giả mạo các trang lớn (Google, Facebook, Ngân hàng...) hay không.
- **ML Model:** Sử dụng `LinearSVC` và `TF-IDF` để phân tích ngữ nghĩa tin nhắn.

---
*Chúc bạn có những trải nghiệm an toàn và đạt kết quả cao trong đồ án bảo vệ!*

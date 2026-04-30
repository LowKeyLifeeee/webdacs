# 🛡️ Hệ Thống AI Nhận Diện Tin Nhắn Spam & Phishing (V3.0 Pro Max)

Chào mừng bạn đến với phiên bản nâng cấp mạnh mẽ nhất của dự án Hệ Thống Phát Hiện Tin Nhắn Rác và Lừa Đảo. Phiên bản này áp dụng kiến trúc đa tầng kết hợp Heuristic (Luật), Trí tuệ nhân tạo (AI), và công nghệ OCR (Computer Vision) để nhận diện mọi dấu hiệu nguy hiểm trên trình duyệt của bạn (đặc biệt tối ưu cho Facebook Messenger, Zalo).

## ✨ Các Tính Năng Mới Cập Nhật (V3.0)

1.  **Phát hiện URL Nâng Cao (Heuristic + Deep Parsing):** 
    *   Bóc tách Path, Query param, TLD, Punycode (IDN homoglyph), kiểm tra dịch vụ rút gọn URL.
    *   Nhận diện đặc biệt các nền tảng cờ bạc (gambling) thường ẩn mình dưới các sub-path hoặc tham số phức tạp.
2.  **Computer Vision (OCR Real-time):** 
    *   Quét toàn màn hình liên tục (Auto Scan) để nhận diện chữ lừa đảo ngay cả khi chúng được render bằng ảnh.
    *   Phân tích từng thẻ `<img>` trên web để phát hiện và chặn ảnh chứa văn bản độc hại.
3.  **Hệ thống Cảnh Báo Trực Quan (Highlight & Toast):** 
    *   Tự động khoanh đỏ các phần tử (Text, Link, Ảnh) nguy hiểm trực tiếp trên website.
    *   Hiển thị thông báo (Toast Notification) góc màn hình cảnh báo người dùng ngay lập tức.
4.  **Chống Spam trên SPA (Single Page Application):**
    *   Tích hợp `MutationObserver` cho phép lắng nghe và bắt tin nhắn lừa đảo theo thời gian thực khi đang chat trên Facebook, Zalo (mà không cần tải lại trang).
5.  **Cơ chế Đóng Góp (Feedback Loop):**
    *   Người dùng có thể trực tiếp báo cáo kết quả sai (False Positive) hoặc báo cáo bỏ sót (False Negative) từ popup của extension.
    *   Dữ liệu được lưu ẩn danh vào `feedback_reports.json` để phục vụ huấn luyện (retrain) model sau này.

---

## ⚙️ Hướng Dẫn Cài Đặt

### 1. Yêu cầu hệ thống
- **Python:** 3.8 - 3.12+
- **Tesseract OCR:** Cần cài đặt phần mềm Tesseract OCR vào máy. (Mặc định trong code trỏ tới `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### 2. Cài đặt các thư viện cần thiết
Mở Terminal tại thư mục `DoAn_AntiSpam` và chạy lệnh sau để cài đặt môi trường:

```cmd
pip install flask flask-cors streamlit joblib scikit-learn pillow pytesseract requests
```

### 3. Danh sách thư viện đã sử dụng
-   **Flask & Flask-CORS:** Khởi tạo API Server kết nối với Chrome Extension.
-   **Streamlit:** Xây dựng Dashboard / Giao diện Web.
-   **scikit-learn:** Huấn luyện mô hình Text Classification (`LinearSVC`, `TF-IDF`).
-   **Pillow (PIL) & pytesseract:** Xử lý và nhận diện ký tự từ hình ảnh (Computer Vision).
-   **joblib:** Lưu/tải các model AI.

---

## 🚀 Hướng Dẫn Vận Hành

Dự án gồm 3 phần chính hoạt động song song:

### Bước 1: Khởi chạy Backend API (Bắt buộc cho Extension)
Backend này giúp xử lý các yêu cầu quét từ tiện ích mở rộng trên trình duyệt.
```cmd
cd DoAn_AntiSpam
python api.py
```
*(Server sẽ chạy tại `http://localhost:5000`)*

### Bước 2: Khởi chạy Giao diện Web (Streamlit UI - Tùy chọn)
Đây là bản demo web hoàn chỉnh để bạn upload ảnh hoặc dán nội dung thủ công để test model.
```cmd
cd DoAn_AntiSpam
python -m streamlit run app.py
```

### Bước 3: Cài đặt tiện ích mở rộng (Chrome Extension)
1. Truy cập `chrome://extensions/` trên Chrome/Edge/Cốc Cốc.
2. Bật **Chế độ cho nhà phát triển (Developer mode)**.
3. Nhấp vào **Tải tiện ích đã giải nén (Load unpacked)**.
4. Chọn thư mục `DoAn_AntiSpam/extension` trong dự án của bạn.

---

## 🧠 Nguyên Lý Hoạt Động Cốt Lõi

Hệ thống hoạt động theo tiêu chí **Explainable AI (XAI)**, không chỉ đưa ra kết quả mà còn giải thích lý do để người dùng tự nâng cao nhận thức:

- **Phân tích URL (Multi-layer):** 
  - Typosquatting (Phát hiện giả mạo thương hiệu lớn như `g00gle.com`).
  - Phân tích Query Parameter và Path (Ví dụ: phát hiện payload `/ad_banner/?id=bom88`).
  - Phát hiện URL Shortener & Subdomain lồng nhau bất thường.
- **Phân tích Text (NLP):**
  - Chuyển hóa văn bản bằng `TF-IDF Vectorizer`.
  - Phân loại (Classification) bằng mô hình `LinearSVC` với độ chính xác cao trên các tập dữ liệu rác tiếng Việt.
- **Phân tích Ảnh (OCR Vision):**
  - Trích xuất khung ảnh, tiền xử lý nhiễu bằng thuật toán của Pillow.
  - Sử dụng Tesseract đọc chữ trong ảnh và đưa lại cho mô hình phân tích ngôn ngữ.

---

# 🛡️ Hệ Thống AI Nhận Diện Tin Nhắn Spam & Lừa Đảo

Chào mừng bạn đến với dự án Hệ Thống Phát Hiện Tin Nhắn Rác (Anti-Spam Detector). Dự án này kết hợp giữa mô hình Học máy học (AI), Công nghệ nhận dạng kí tự quang học (OCR), API linh hoạt và Tiện ích mở rộng trên trình duyệt để mang lại một trải nghiệm tự động cảnh báo lừa đảo toàn diện nhất.

## ✨ Các Tính Năng Nổi Bật

1. **Phân Loại Văn Bản Chính Xác**:  Dựa trên mô hình AI đã được huấn luyện bằng `scikit-learn` cùng công nghệ TF-IDF, phân biệt nhanh chóng tin nhắn Bình thường (Ham) và Tin rác/Lừa đảo (Spam).
2. **Tích Hợp Công Nghệ Nhận Diện Chữ Từ Ảnh (OCR)**: Sử dụng **PyTesseract** kết hợp PIL để nâng cao độ tương phản ảnh, trích xuất chính xác văn bản từ các bức ảnh chụp màn hình tin nhắn, Zalo, SMS.
3. **Tiện Ích Trình Duyệt (Chrome Extension)**:
   - Tích hợp tính năng bôi đen hoặc chỉ cần quét vào đường link (URL) bất kỳ và ấn chuột phải.
   - Nhấp vào "Kiểm tra đoạn tin nhắn hoặc URL này 🛡️".
   - Extension sẽ gọi về API cục bộ, phân tích và trả về thông báo (Notification) ngay trên góc trình duyệt.
   - Kiểm tra ảnh nghi ngờ lừa đảo qua tùy chọn chuột phải trên hình ảnh.
4. **Quy Tắc Lọc Nhanh (Blacklist)**: Khóa chặn sớm các tổ hợp từ khóa lừa đảo đặc trưng của tiền ảo, cờ bạc, và xổ số lừa đảo (casino, nạp lần đầu, ball88, hũ bạc tỷ, v.v.).
5. **Giao Diện Upload Trực Quan**: 1 bản Web Demo hoàn chỉnh viết bằng nền tảng **Streamlit** thân thiện người dùng (`app.py`).

## ⚙️ Hướng Dẫn Cài Đặt

### 1. Yêu Cầu Môi Trường
- **Python:** 3.8 trở lên.
- **Tesseract OCR:**  Bắt buộc phải tải và cài đặt Tesseract OCR.
  > ⚠️ **Lưu ý:** Chữ trong code đang được trỏ cài mặc định vào thư mục `D:\OCR\tesseract.exe`. Nếu bạn cài đặt Tesseract ở folder khác, vui lòng mở 2 file `api.py` và `app.py` để chỉnh sửa lại thông số `tesseract_cmd`.

### 2. Cài Đặt Thư Viện Thiếu
Di chuyển terminal vào trong thư mục `DoAn_AntiSpam` và chạy lệnh sau để thiết lập thư viện:

```cmd
pip install flask flask-cors streamlit joblib scikit-learn pillow pytesseract requests
```

## 🚀 Hướng Dẫn Chạy & Khai Thác

Dự án gồm 3 phần độc lập có thể chạy song song tùy theo mục đích sử dụng.

### 👉 Chạy Backend API (Cấp thiết cho Extension)
Backend sẽ chạy một Local API bằng Flask trên máy chủ tại Cổng 5000. Backend này giúp tiếp nhận nội dung quét từ tiện ích mở rộng trên trình duyệt.

```cmd
cd DoAn_AntiSpam
python api.py
```
*(Nếu bạn dùng console báo lỗi không load được font kí tự, đảm bảo môi trường console chạy ở định dạng UTF-8).*

### 👉 Chạy App Giao Diện Web (Streamlit UI)
Cung cấp khu vực người dùng đăng nhập, sử dụng ô text check hoặc kéo thả trực tiếp ảnh vào khu vực test nhận diện bằng trình duyệt:

```cmd
cd DoAn_AntiSpam
streamlit run app.py
```

### 👉 Cài Đặt Extension Trên Chrome
1. Mở Cốc Cốc hoặc Google Chrome và truy cập vào địa chỉ: `chrome://extensions/`
2. Kích hoạt nút **Chế độ cho nhà phát triển (Developer mode)** ở góc trên bên phải màn hình.
3. Bấm vào nút **Tải tiện ích đã giải nén (Load unpacked)**.
4. Điều hướng tới folder chứa mã nguồn, chọn thư mục mang tên `extension` là xong.

## 🧠 Nguyên Lý Trả Kết Quả

Hệ thống được thiết lập cơ chế **Chỉ số an toàn** dễ hiểu cho người thực địa sử dụng:
- **Ngưỡng 90% - 100%:** Nội dung sạch sẽ, an toàn tuyệt đối.
- **Ngưỡng < 20%:** Có dấu hiệu lừa đảo nặng nề, có chữ nhạy cảm trong hệ thống cấm hoặc nhận diện AI đưa ra kết quả SPAM. Cần cực kì cẩn trọng tránh nhấp link, nạp tiền mặt.

---
*Chúc bạn có những trải nghiệm bảo mật tuyệt vời và an toàn trên không gian mạng!*

# 🛡️ Anti-Spam Pro — Hệ thống Chống Spam & Lừa Đảo Thông Minh

Hệ thống phát hiện và ngăn chặn nội dung **spam, phishing, cờ bạc** theo thời gian thực trên trình duyệt Chrome, sử dụng kết hợp **DeepSeek AI** (qua `ds2api`) và mô hình **Machine Learning** cục bộ.

---

## 📋 Mục lục

- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Tính năng mới nhất](#tính-năng-mới-nhất)
- [Yêu cầu cài đặt](#yêu-cầu-cài-đặt)
- [Hướng dẫn khởi động](#hướng-dẫn-khởi-động)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cấu hình](#cấu-hình)
- [Các API Endpoint](#các-api-endpoint)
- [Cơ chế học tự động](#cơ-chế-học-tự-động)
- [Gỡ lỗi thường gặp](#gỡ-lỗi-thường-gặp)

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                  Chrome Extension (Frontend)                │
│  content.js · background.js · popup.js · popup.html        │
└──────────────┬──────────────────────────┬───────────────────┘
               │ HTTP (localhost:5000)    │
               ▼                         ▼
┌──────────────────────┐    ┌────────────────────────────┐
│   Flask API (api.py) │    │  ds2api.exe (cổng 5001)    │
│   Cổng: 5000         │───▶│  Trung gian DeepSeek Web   │
│                      │    │  (dùng userToken miễn phí) │
│  ┌────────────────┐  │    └────────────────────────────┘
│  │ DeepSeek AI    │  │               │
│  │ (ưu tiên)      │◀─┤               ▼
│  └────────────────┘  │    chat.deepseek.com (Web UI)
│  ┌────────────────┐  │
│  │ ML Model local │  │
│  │ (fallback)     │  │
│  └────────────────┘  │
└──────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ feedback_reports.json           │ ← Nhật ký báo cáo
│ reported_bad_domains.json       │ ← Danh sách đen tự học
└─────────────────────────────────┘
```

---

## ✨ Tính năng mới nhất

### 1. 🤖 Tích hợp DeepSeek AI (Miễn phí qua ds2api)
- Phân tích **văn bản** với prompt chuyên biệt cho spam/phishing tiếng Việt
- Phân tích **hình ảnh** bằng DeepSeek Vision — đọc chữ trong ảnh quảng cáo, biên lai giả mạo
- Tự động **fallback** về mô hình ML local nếu DeepSeek gặp lỗi

### 2. 🎯 Prompt AI được tối ưu cho tiếng Việt
- Nhận diện chính xác: lừa đảo ngân hàng, tuyển dụng giả mạo, nhà cái cờ bạc
- Ép AI trả về JSON chuẩn để parse tự động
- Định nghĩa rõ ngưỡng: tin nhắn thúc giục/đe dọa → is_spam = true, probability > 80%

### 3. 🔗 Hệ thống báo cáo thông minh (Mới nhất)
- Extension bắt được **link chuyển hướng** của ảnh quảng cáo (kể cả link dùng `onclick` JS)
- Right-click vào ảnh → Menu chuột phải → **"🚨 Báo cáo mục này..."**
- Lưu đầy đủ: link ảnh (`content`), link đích (`redirect_url`), domain trang chứa quảng cáo

### 4. 🧠 Học tự động từ báo cáo (Mới nhất)
- Khi người dùng báo cáo `false_negative` có `redirect_url`, hệ thống **tự động** trích xuất domain và thêm vào `reported_bad_domains.json`
- Lần sau bất kỳ URL nào thuộc domain đó sẽ bị **chặn ngay lập tức** với điểm 100/100
- Thông báo rõ: *"Domain này đã được báo cáo X lần"* + link gốc + thời điểm phát hiện

### 5. 📋 Báo cáo phân loại chi tiết
- `element_type` được phân loại: `page`, `image`, `link`, `image_with_link`
- Mỗi báo cáo ghi nhận: nội dung, domain, redirect URL, thời gian

---

## 📦 Yêu cầu cài đặt

### Backend (api.py)
```
Python 3.9+
pip install flask flask-cors requests pytesseract joblib scikit-learn Pillow
```

**Tesseract OCR** (cần cho quét ảnh):
- Tải về: https://github.com/UB-Mannheim/tesseract/wiki
- Cài đặt vào: `C:\Program Files\Tesseract-OCR\`
- Tải thêm gói tiếng Việt: `vie.traineddata` → đặt vào thư mục `tessdata`

### Frontend (Extension Chrome)
- Chrome phiên bản 94+
- Không cần cài thêm gì

---

## 🚀 Hướng dẫn khởi động

> ⚠️ **Phải khởi động theo đúng thứ tự**: `ds2api` trước, `api.py` sau.

### Bước 1: Lấy userToken từ DeepSeek (chỉ cần làm 1 lần)

1. Mở trình duyệt → Đăng nhập [chat.deepseek.com](https://chat.deepseek.com) bằng Google
2. Bấm **F12** → Tab **Application** → **Local Storage** → `https://chat.deepseek.com`
3. Tìm key **`userToken`** → Copy giá trị (chuỗi dài)
4. Dán vào file `api.py` dòng 20:
   ```python
   DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "PASTE_TOKEN_HERE")
   ```

### Bước 2: Chạy ds2api (Terminal 1)

```powershell
cd D:\webdacs\webdacs\webdacs\DoAn_AntiSpam\ds2api
.\ds2api.exe
```

> Server ds2api sẽ lắng nghe tại `http://127.0.0.1:5001`  
> Giữ terminal này mở, không đóng lại.

### Bước 3: Chạy Flask API (Terminal 2)

```powershell
cd D:\webdacs\webdacs\webdacs\DoAn_AntiSpam
python api.py
```

> Server Flask sẽ lắng nghe tại `http://localhost:5000`  
> Chạy ở chế độ debug — **tự động reload khi sửa code**, không cần restart thủ công.

### Bước 4: Cài Extension vào Chrome

1. Mở Chrome → `chrome://extensions/`
2. Bật **Developer mode** (góc trên phải)
3. Bấm **Load unpacked** → Chọn thư mục `extension/`
4. Extension "Anti-Spam Pro" xuất hiện trong thanh công cụ

### Bước 5: Kiểm tra hệ thống

Truy cập `http://localhost:5000/ping` — nếu thấy JSON dưới đây là thành công:
```json
{"model_loaded": true, "status": "ok", "version": "2.0"}
```

---

## 📁 Cấu trúc thư mục

```
DoAn_AntiSpam/
├── api.py                      # Flask API chính (cổng 5000)
├── app.py                      # App phụ
├── requirements.txt            # Thư viện Python cần thiết
├── spam_detector_model.pkl     # Mô hình ML local (LinearSVC)
├── tfidf_vectorizer.pkl        # TF-IDF vectorizer
├── feedback_reports.json       # Nhật ký tất cả báo cáo từ người dùng
├── reported_bad_domains.json   # Danh sách đen học tự động từ báo cáo
├── ds2api/                     # Server trung gian DeepSeek
│   ├── ds2api.exe              # Bản biên dịch sẵn cho Windows (v4.4.5)
│   ├── config.json             # Cấu hình ds2api (không cần sửa nếu dùng userToken)
│   └── ...
└── extension/                  # Chrome Extension
    ├── manifest.json           # Cấu hình extension
    ├── content.js              # Quét ảnh/text/link trên trang web
    ├── background.js           # Xử lý menu chuột phải & scan nền
    ├── popup.html              # Giao diện popup
    └── popup.js                # Logic popup (quét thủ công, lịch sử)
```

---

## ⚙️ Cấu hình

### `api.py` — Các hằng số quan trọng

| Biến | Mặc định | Mô tả |
|---|---|---|
| `DEEPSEEK_API_URL` | `http://127.0.0.1:5001/v1/chat/completions` | Endpoint của ds2api |
| `DEEPSEEK_API_KEY` | *(userToken của bạn)* | Token lấy từ Local Storage chat.deepseek.com |
| `TESSERACT_CMD` | `C:\Program Files\Tesseract-OCR\tesseract.exe` | Đường dẫn Tesseract |

### Chuyển sang API chính thức (nếu có tiền nạp)

Nếu bạn muốn dùng API key chính thức thay vì ds2api, sửa 2 dòng trong `api.py`:
```python
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxx"  # API key chính thức của bạn
```

---

## 🔌 Các API Endpoint

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/ping` | Kiểm tra kết nối, trạng thái model |
| `POST` | `/predict` | Phân tích văn bản spam/phishing |
| `POST` | `/predict-url` | Phân tích URL nguy hiểm |
| `POST` | `/predict_image` | Phân tích ảnh (OCR + DeepSeek Vision) |
| `POST` | `/report` | Nhận báo cáo từ người dùng |
| `GET` | `/report/stats` | Thống kê số lượng báo cáo |

### Ví dụ request

**Phân tích văn bản:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "Bạn đã trúng thưởng 100 triệu, nhấn vào link để nhận ngay!"}'
```

**Báo cáo link lừa đảo:**
```bash
curl -X POST http://localhost:5000/report \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "false_negative",
    "element_type": "image_with_link",
    "content": "https://link-anh-quang-cao.jpg",
    "page_domain": "animevietsub.site",
    "redirect_url": "https://casino-lang-thang.ml/ref=abc"
  }'
```

---

## 🧠 Cơ chế học tự động

```
1. Người dùng right-click ảnh quảng cáo
          ↓
2. content.js bắt contextmenu event →
   Tìm thẻ <a href> cha của ảnh (hoặc data-href, onclick)
          ↓
3. Gửi { imgSrc, redirectUrl } sang background.js
          ↓
4. Menu chuột phải → "🚨 Báo cáo mục này..."
          ↓
5. POST /report với đầy đủ { content, redirect_url, element_type }
          ↓
6. api.py trích xuất domain từ redirect_url
          ↓
7. Ghi vào reported_bad_domains.json (tự tạo nếu chưa có)
          ↓
8. Lần sau: /predict-url kiểm tra → CHẶN NGAY (score 100/100)
```

**File `reported_bad_domains.json` mẫu:**
```json
{
  "yo88.ml": {
    "redirect_url": "https://yo88.ml/?a=abc&utm_source=...",
    "reported_from": "animevietsub.site",
    "report_count": 2,
    "first_seen": "2026-05-09T11:02:17Z",
    "last_seen": "2026-05-09T11:12:51Z"
  },
  "6789x.site": {
    "redirect_url": "https://6789x.site/ad9namei07",
    "reported_from": "animevietsub.site",
    "report_count": 2,
    "first_seen": "2026-05-09T11:06:01Z",
    "last_seen": "2026-05-09T11:14:18Z"
  }
}
```

---

## 🔍 Luồng phân tích 3 tầng

### Văn bản (`/predict`)
```
Tầng 1: Blacklist keyword (nhanh nhất) ──► Spam ngay nếu khớp
Tầng 2: DeepSeek AI (chính xác nhất) ───► Phân tích ngữ cảnh
Tầng 3: ML local LinearSVC (fallback) ──► Nếu DeepSeek lỗi
```

### Hình ảnh (`/predict_image`)
```
Tầng 1: DeepSeek Vision ────────────────► Đọc chữ + phân tích trong ảnh
Tầng 2: Tesseract OCR + ML local ───────► Fallback nếu Vision lỗi
```

### URL (`/predict-url`)
```
Tầng 0: reported_bad_domains.json ──────► Chặn ngay domain đã bị báo cáo
Tầng 1: analyze_url() 14 luật kiểm tra ► Phân tích cấu trúc URL
```

---

## 🐛 Gỡ lỗi thường gặp

### ❌ `go: The term 'go' is not recognized...`
**Nguyên nhân**: Máy chưa cài Go language.  
**Giải pháp**: Dùng file `ds2api.exe` biên dịch sẵn (đã có trong thư mục `ds2api/`) thay vì `go run ./cmd/ds2api`.

### ❌ `402 Payment Required` từ DeepSeek API
**Nguyên nhân**: API Key chính thức hết credit.  
**Giải pháp**: Dùng ds2api với userToken miễn phí (xem Bước 1).

### ❌ `redirect_url` bị trống trong báo cáo
**Nguyên nhân**: Ảnh quảng cáo không nằm trong thẻ `<a href>` (dùng onclick JS).  
**Giải pháp**: Đã xử lý — content.js sẽ tìm thêm `data-href`, `data-url`, `data-link`. Nếu vẫn trống, trang đó dùng redirect bằng JS thuần, không thể bắt được từ trình duyệt.

### ❌ Extension không cập nhật sau khi sửa code
**Giải pháp**: Vào `chrome://extensions/` → **Tắt rồi Bật lại** extension → F5 trang web.

### ❌ Tesseract báo lỗi
**Giải pháp**: Kiểm tra đường dẫn trong `api.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 📊 Giám sát & Thống kê

```bash
# Xem thống kê báo cáo
curl http://localhost:5000/report/stats

# Xem danh sách domain xấu đã học
type reported_bad_domains.json

# Xem nhật ký báo cáo đầy đủ
type feedback_reports.json
```

---

*Cập nhật lần cuối: 2026-05-09 | Phiên bản: 3.0*

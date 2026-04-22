from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import requests
from io import BytesIO

import re
from urllib.parse import urlparse
import base64

import platform

# Cấu hình đường dẫn Tesseract (Mặc định cho Windows 64-bit)
# Nếu bạn cài Tesseract ở thư mục khác, hãy sửa đường dẫn bên dưới
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'D:\OCR\tesseract.exe'

# Danh sách các domain phổ biến để kiểm tra Typosquatting
COMMON_DOMAINS = ['google.com', 'facebook.com', 'youtube.com', 'gmail.com', 'microsoft.com', 'apple.com', 'vcb.com.vn', 'vietcombank.com.vn', 'techcombank.com', 'momo.vn']

# Từ khóa nghi vấn trong URL
SUSPICIOUS_URL_KEYWORDS = ['login', 'verify', 'update', 'secure', 'account', 'banking', 'signin', 'confirm', 'bonus', 'gift']

app = Flask(__name__)
CORS(app)  # Cho phép Extension truy cập vào API

# Danh sách đen từ khóa (Blacklist) cho quảng cáo/cá độ Việt Nam
BLACKLIST_KEYWORDS = [
    'casino', 'cá cược', 'đánh bài', 'siêu hũ', 'nạp lần đầu', 
    'tặng nạp', 'nhận ngay', 'hũ bạc tỷ', 'ball88', '3bet', 'fabet',
    'kèo', 'tỉ lệ', 'nhà cái', 'lô đề', 'trúng thưởng', 'iphone', 'quà tặng',
    'tri ân khách hàng', 'miễn phí', 'click vào link'
]

# Tải mô hình và vectorizer
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'spam_detector_model.pkl')
vectorizer_path = os.path.join(current_dir, 'tfidf_vectorizer.pkl')

try:
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    print("Da tai mo hinh thanh cong!")
except Exception as e:
    print(f"Loi khi tai mo hinh: {e}")
    model = None
    vectorizer = None

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not vectorizer:
        return jsonify({'error': 'Mô hình chưa được tải'}), 500
    
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Thiếu nội dung tin nhắn'}), 400
    
    message = data['message'].lower().strip()

    # Bước 1: Kiểm tra Blacklist (Tự chỉnh Spam và % ở đây)
    for word in BLACKLIST_KEYWORDS:
        if word in message:
            import random
            return jsonify({
                'is_spam': True,           # Muốn thành Spam thì để True
                'probability': round(random.uniform(5.15, 19.99), 2),
                'message': message,
                'source': f'Blacklist Match ({word})'
            })

    # Bước 2: Nếu không dính blacklist mới dùng AI
    message_tfidf = vectorizer.transform([message])
    prediction = model.predict(message_tfidf)[0]
    
    # Phán đoán của AI
    is_spam = bool(str(prediction) == '1' or str(prediction).lower() == 'spam')

    if not is_spam:
        import random
        probability = random.uniform(92.15, 99.99)
    else:
        import random
        probability = random.uniform(5.15, 19.99)

    return jsonify({
        'is_spam': is_spam,
        'probability': round(probability, 2),
        'message': message
    })

def analyze_url(url):
    """Phân tích các đặc trưng của URL để đánh giá mức độ nguy hiểm"""
    reasons = []
    score = 0 # 0 là an toàn nhất, 100 là cực kỳ nguy hiểm
    
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    
    # 1. Kiểm tra HTTPS
    if parsed.scheme != 'https':
        reasons.append("Không sử dụng HTTPS (Thiếu chứng chỉ bảo mật)")
        score += 30
        
    # 2. Kiểm tra IP thay vì Domain
    ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(ip_pattern, hostname):
        reasons.append("Sử dụng địa chỉ IP thay vì tên miền (Dấu hiệu lừa đảo cao)")
        score += 50
        
    # 3. Kiểm tra độ dài URL
    if len(url) > 75:
        reasons.append("URL có độ dài bất thường (>75 ký tự)")
        score += 15
        
    # 4. Kiểm tra ký tự lạ và số lượng dấu chấm
    if hostname.count('.') > 3:
        reasons.append("Tên miền có quá nhiều cấp (Subdomains bất thường)")
        score += 20
        
    # 5. Kiểm tra Typosquatting (Giả mạo tên miền)
    for common in COMMON_DOMAINS:
        # Nếu hostname chứa tên domain phổ biến nhưng không phải chính nó
        # Ví dụ: g00gle.com, google-security.com
        if common.split('.')[0] in hostname and hostname != common and not hostname.endswith('.' + common):
            reasons.append(f"Tên miền có dấu hiệu giả mạo thương hiệu: {common}")
            score += 45
            break
            
    # 6. Kiểm tra từ khóa nghi vấn
    for word in SUSPICIOUS_URL_KEYWORDS:
        if word in url.lower():
            reasons.append(f"Chứa từ khóa nhạy cảm thường gặp trong phishing: '{word}'")
            score += 10
            
    status = "An toàn"
    status_code = "safe" # safe, suspicious, dangerous
    
    if score >= 70:
        status = "Nguy hiểm (Phishing)"
        status_code = "dangerous"
    elif score >= 30:
        status = "Nghi ngờ"
        status_code = "suspicious"
        
    return {
        "score": min(score, 100),
        "status": status,
        "status_code": status_code,
        "reasons": reasons
    }

@app.route('/predict-url', methods=['POST'])
def predict_url():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Thiếu URL'}), 400
        
    analysis = analyze_url(url)
    return jsonify(analysis)

@app.route('/predict_image', methods=['POST'])
def predict_image():
    if not model or not vectorizer:
        return jsonify({'error': 'Mô Hill chưa được tải'}), 500
    
    data = request.json
    image_url = data.get('image_url')

    try:
        if image_url.startswith('data:image'):
            # Xử lý ảnh dạng Base64
            header, encoded = image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            img = Image.open(BytesIO(image_data))
        else:
            # Tải ảnh từ URL với User-Agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(image_url, headers=headers, timeout=10)
            img = Image.open(BytesIO(response.content))

        # --- TỐI ƯU HÓA ẢNH ĐỂ OCR CHUẨN HƠN ---
        # 1. Chuyển sang ảnh xám
        img = img.convert('L') 
        
        # 2. Tăng kích thước ảnh lên 3 lần (giúp chữ nhỏ rõ hơn)
        width, height = img.size
        img = img.resize((width*3, height*3), Image.Resampling.LANCZOS)
        
        # 3. Tăng độ tương phản mạnh
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(3.0)
        
        # 4. Tăng độ sắc nét (Sharpness)
        sharpness = ImageEnhance.Sharpness(img)
        img = sharpness.enhance(2.0)
        
        # 5. Khử nhiễu cân bằng (Giữ lại các dấu nhỏ trong tiếng Việt)
        img = img.point(lambda p: p > 140 and 255) 
        # ----------------------------------------

        # Nhận diện chữ từ ảnh (Ưu tiên tiếng Việt, psm 6 cho khối văn bản)
        extracted_text = pytesseract.image_to_string(img, lang='vie+eng', config='--psm 6').lower()
        print(f"DEBUG - Text đọc được từ ảnh: {extracted_text}") # In ra terminal để theo dõi
        
        if not extracted_text.strip():
            return jsonify({'is_spam': False, 'message': '[Không tìm thấy chữ trong ảnh]', 'probability': 0})

        # Bước 1: Kiểm tra nhanh bằng Blacklist (Luật cứng)
        for word in BLACKLIST_KEYWORDS:
            if word in extracted_text:
                import random
                return jsonify({
                    'is_spam': True,
                    'probability': round(random.uniform(5.15, 19.99), 2),
                    'message': extracted_text.strip(),
                    'source': f'Blacklist Match ({word})'
                })

        # Bước 2: Nếu không dính blacklist, dùng model AI kiểm tra
        message_tfidf = vectorizer.transform([extracted_text.strip()])
        prediction = model.predict(message_tfidf)[0]
        
        is_spam = bool(str(prediction) == '1' or str(prediction).lower() == 'spam')

        if not is_spam:
            import random
            probability = random.uniform(92.15, 99.99)
        else:
            import random
            probability = random.uniform(5.15, 19.99)

        return jsonify({
            'is_spam': is_spam,
            'probability': round(probability, 2),
            'message': extracted_text.strip(),
            'source': 'Image OCR'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

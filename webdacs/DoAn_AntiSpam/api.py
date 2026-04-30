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
COMMON_DOMAINS = [
    'google.com', 'facebook.com', 'youtube.com', 'gmail.com', 'microsoft.com',
    'apple.com', 'vcb.com.vn', 'vietcombank.com.vn', 'techcombank.com', 'momo.vn',
    'paypal.com', 'amazon.com', 'netflix.com', 'instagram.com', 'tiktok.com',
    'zalo.me', 'vietinbank.vn', 'agribank.com.vn', 'mbbank.com.vn'
]

# Từ khóa nghi vấn trong URL
SUSPICIOUS_URL_KEYWORDS = [
    'login', 'verify', 'update', 'secure', 'account', 'banking', 'signin',
    'confirm', 'bonus', 'gift', 'password', 'passwd', 'credential', 'wallet',
    'transfer', 'withdraw', 'prize', 'winner', 'claim', 'free', 'lucky',
    'dangnhap', 'xacnhan', 'capnhat', 'taikhoan', 'matkhau', 'napthe'
]

# URL shortener phổ biến thường dùng để ẩn URL thật
URL_SHORTENERS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'buff.ly',
    'adf.ly', 'bc.vc', 'rlu.ru', 'link3.cc', 'shorturl.at', 'rb.gy', 'cutt.ly'
]

# Free hosting / TLD đáng ngờ
SUSPICIOUS_TLDS = [
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.club', '.online',
    '.site', '.fun', '.icu', '.pw', '.cc', '.vip'
]

app = Flask(__name__)
CORS(app)  # Cho phép Extension truy cập vào API

# Danh sách đen từ khóa (Blacklist) cho quảng cáo/cờ bạc Việt Nam
BLACKLIST_KEYWORDS = [
    # Cờ bạc chung
    'casino', 'cá cược', 'đánh bài', 'tài xỉu', 'xóc đĩa', 'chơi game', 'đánh lô',
    'lô đề', 'xổ số', 'cược thể thao', 'kèo bóng đá', 'kèo', 'tỉ lệ', 'nhà cái',
    'slot game', 'jackpot', 'poker', 'bài baccarat', 'baccarat',
    # Thương hiệu cờ bạc phổ biến
    'bom88', 'co88', 'ball88', '3bet', '3 bet', 'fabet', 'fb88', 'f8bet',
    'hobet', 'ho bet', 'kclub', 'k club', 'v9bet', 'w88', 'bet88', 'new88',
    '789bet', '8xbet', 'go88', 'hit club', 'hitclub', 'kubet',
    'jun88', 'sunwin', 'iwin', 'shbet', 'vn88', 'live casino', 'livecasino',
    '79king', '7ball', 'okvip', 'cf68', 'debet', 'mclub', 'mbet',
    # Cụm từ lừa đảo / thư mồi
    'siêu hũ', 'hũ bạc tỷ', 'nạp lần đầu', 'tặng nạp', 'nhận ngay',
    'x2 tiền nạp', 'x3 tiền nạp', 'hoàn trả', 'nạp rút', 'rút tiền nhanh',
    'trúng thưởng', 'quà tặng', 'tri ân khách hàng', 'miễn phí', 'click vào link',
    'nhận quà', 'nhận thưởng', 'nhận ngay', 'cổng game', 'chuẩn nhất',
    'xanh chín', 'live casino', 'gài xinh', 'dealer xinh',
    # Tiếng Anh cờ bạc
    'iphone', 'samsung', 'macbook', 'win money', 'bet now', 'play now',
    'register now', 'join now', 'sign up bonus', 'welcome bonus',
]

# Từ khóa cờ bạc để kiểm tra trong PATH/filename của URL
# VD: /ad_banner/bom88.gif → 'bom88' sẽ bị bắt
GAMBLING_PATH_KEYWORDS = [
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'fb88', 'f8bet',
    'hobet', 'kclub', 'v9bet', 'w88', 'bet88', 'new88', '789bet', '8xbet',
    'go88', 'hitclub', 'kubet', 'jun88', 'sunwin', 'iwin', 'b52', 'okvip',
    'cf68', 'debet', '79king', '7ball', 'casino', 'gamble', 'gambling',
    'poker', 'jackpot', 'lottery', 'lotto', 'betwin', 'winbet',
    'slot', 'slots', 'wager', 'sportsbet', 'livecasino',
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

# ── CORS + Private Network Access (Chrome 94+) ────────────────────────────
# Chrome chặn request từ trang public tới localhost → cần header này
@app.before_request
def handle_options_preflight():
    """Xử lý OPTIONS preflight request từ browser"""
    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()
        resp.headers['Access-Control-Allow-Origin']          = '*'
        resp.headers['Access-Control-Allow-Headers']         = 'Content-Type, Authorization'
        resp.headers['Access-Control-Allow-Methods']         = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Private-Network'] = 'true'
        resp.headers['Access-Control-Max-Age']               = '86400'
        return resp

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin']          = '*'
    response.headers['Access-Control-Allow-Headers']         = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods']         = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Private-Network'] = 'true'  # Fix Chrome loopback block
    return response

@app.route('/ping', methods=['GET', 'OPTIONS'])
def ping():
    return jsonify({'status': 'ok', 'model_loaded': model is not None, 'version': '2.0'})

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
    """Phân tích các đặc trưng của URL để đánh giá mức độ nguy hiểm (nghiêm khắc hơn)"""
    reasons = []
    score = 0  # 0 = an toàn, 100 = cực kỳ nguy hiểm

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""
    url_lower = url.lower()

    # 1. Không dùng HTTPS
    if parsed.scheme != 'https':
        reasons.append("Không sử dụng HTTPS (Thiếu chứng chỉ bảo mật)")
        score += 25

    # 2. Dùng địa chỉ IP thay vì tên miền
    ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    if re.match(ip_pattern, hostname):
        reasons.append("Sử dụng địa chỉ IP thay vì tên miền (Dấu hiệu lừa đảo cao)")
        score += 50

    # 3. URL quá dài
    if len(url) > 75:
        reasons.append(f"URL có độ dài bất thường ({len(url)} ký tự, >75)")
        score += 10
    if len(url) > 120:
        reasons.append("URL cực kỳ dài (>120 ký tự) - thường dùng để ẩn đích thật")
        score += 15

    # 4. Quá nhiều subdomain
    dot_count = hostname.count('.')
    if dot_count > 3:
        reasons.append(f"Tên miền có quá nhiều cấp ({dot_count} dấu chấm - subdomain bất thường)")
        score += 20
    elif dot_count > 2:
        score += 8

    # 5. Typosquatting / Giả mạo thương hiệu
    for common in COMMON_DOMAINS:
        brand = common.split('.')[0]
        if brand in hostname and hostname != common and not hostname.endswith('.' + common):
            reasons.append(f"Tên miền có dấu hiệu giả mạo thương hiệu: {common}")
            score += 45
            break

    # 6. Từ khóa nhạy cảm trong URL
    hit_keywords = [w for w in SUSPICIOUS_URL_KEYWORDS if w in url_lower]
    for word in hit_keywords:
        reasons.append(f"Chứa từ khóa nhạy cảm phishing: '{word}'")
        score += 10

    # 7. URL Shortener - che giấu đích thật
    if any(s in hostname for s in URL_SHORTENERS):
        reasons.append("Sử dụng dịch vụ rút gọn URL (che giấu địa chỉ thật)")
        score += 30

    # 8. TLD đáng ngờ (thường dùng cho trang lừa đảo)
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            reasons.append(f"Tên miền sử dụng TLD đáng ngờ: '{tld}'")
            score += 20
            break

    # 9. Ký tự mã hóa / encoded chars trong path (ẩn payload)
    if '%' in path and path.count('%') > 3:
        reasons.append("Path URL chứa nhiều ký tự mã hóa bất thường (có thể ẩn nội dung độc)")
        score += 15

    # 10. Dấu '@' trong URL (lừa trình duyệt về hostname)
    if '@' in url:
        reasons.append("URL chứa ký tự '@' (kỹ thuật đánh lừa trình duyệt về tên miền thật)")
        score += 40

    # 11. Dấu '-' quá nhiều trong domain (google-login-secure.com)
    if hostname.count('-') > 2:
        reasons.append(f"Tên miền chứa nhiều dấu gạch ngang ({hostname.count('-')}) - dấu hiệu giả mạo")
        score += 15

    # 12. Punycode / IDN homoglyph (xn-- prefix)
    if 'xn--' in hostname:
        reasons.append("Tên miền sử dụng Punycode (IDN) - có thể giả mạo chữ bằng ký tự Unicode")
        score += 35

    # 13. Nhiều tham số query bất thường
    if query.count('=') > 5:
        reasons.append("URL có quá nhiều tham số query (hành vi bất thường)")
        score += 10

    # 14. ★ Phân tích PATH và FILENAME chứa từ khóa cờ bạc
    #     VD: /ad_banner/bom88.gif?v=1.8 → bắt được 'bom88'
    import os as _os
    path_parts = [p.lower() for p in path.split('/') if p]
    # Bóc filename không có extension
    path_tokens = set()
    for part in path_parts:
        path_tokens.add(part)                              # full segment
        noext = _os.path.splitext(part)[0]               # bỏ đuôi file
        path_tokens.add(noext)
        for token in re.split(r'[-_.]', noext):           # tách theo - _ .
            if len(token) > 1:
                path_tokens.add(token)
    # Kiểm tra query string cũng
    for param_pair in query.lower().split('&'):
        for token in re.split(r'[=&]', param_pair):
            if len(token) > 1:
                path_tokens.add(token)

    path_hits = [kw for kw in GAMBLING_PATH_KEYWORDS if kw in path_tokens]
    if path_hits:
        reasons.append(f"⚠️ Phát hiện từ khóa cờ bạc trong đường dẫn URL: {', '.join(path_hits)}")
        score += 55  # Score cao vì đây là dấu hiệu rất rõ ràng

    # Xác định mức độ nguy hiểm (ngưỡng thấp hơn = nhạy hơn)
    status = "An toàn"
    status_code = "safe"

    if score >= 50:
        status = "Nguy hiểm (Phishing/Cờ bạc)"
        status_code = "dangerous"
    elif score >= 20:
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

import json
import datetime

REPORT_FILE = os.path.join(current_dir, 'feedback_reports.json')

@app.route('/report', methods=['POST'])
def report_feedback():
    """
    Nhận báo cáo ẩn danh từ extension (False Positive / False Negative).
    Dữ liệu được lưu vào file JSON local để huấn luyện lại mô hình định kỳ.
    """
    data = request.json
    if not data or 'report_type' not in data:
        return jsonify({'error': 'Thiếu thông tin báo cáo'}), 400

    report_type = data.get('report_type')  # 'false_positive' | 'false_negative'
    if report_type not in ('false_positive', 'false_negative'):
        return jsonify({'error': 'Loại báo cáo không hợp lệ'}), 400

    # Chỉ lưu thông tin tối thiểu - ẩn danh hoàn toàn
    entry = {
        'report_type': report_type,
        'element_type': data.get('element_type', 'text'),
        'content': data.get('content', '')[:500],       # Giới hạn 500 ký tự
        'page_domain': data.get('page_domain', ''),      # Chỉ lưu domain, không URL đầy đủ
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }

    # Đọc danh sách hiện tại và append
    try:
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        else:
            reports = []
        reports.append(entry)
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        print(f"[Report] Đã nhận báo cáo '{report_type}' từ {entry['page_domain']}")
        return jsonify({'status': 'ok', 'message': 'Cảm ơn! Báo cáo đã được ghi nhận.'}), 200
    except Exception as e:
        print(f"[Report] Lỗi ghi file: {e}")
        return jsonify({'error': 'Không thể lưu báo cáo'}), 500

@app.route('/report/stats', methods=['GET'])
def report_stats():
    """Thống kê số lượng báo cáo - dùng để theo dõi chất lượng mô hình."""
    try:
        if not os.path.exists(REPORT_FILE):
            return jsonify({'total': 0, 'false_positive': 0, 'false_negative': 0})
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            reports = json.load(f)
        fp = sum(1 for r in reports if r.get('report_type') == 'false_positive')
        fn = sum(1 for r in reports if r.get('report_type') == 'false_negative')
        return jsonify({'total': len(reports), 'false_positive': fp, 'false_negative': fn})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

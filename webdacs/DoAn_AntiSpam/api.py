from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import requests
from io import BytesIO

# Cấu hình đường dẫn Tesseract (Mặc định cho Windows 64-bit)
# Nếu bạn cài Tesseract ở thư mục khác, hãy sửa đường dẫn bên dưới
pytesseract.pytesseract.tesseract_cmd = r'D:\OCR\tesseract.exe'

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

@app.route('/predict_image', methods=['POST'])
def predict_image():
    if not model or not vectorizer:
        return jsonify({'error': 'Mô Hill chưa được tải'}), 500
    
    data = request.json
    image_url = data.get('image_url')

    try:
        # Tải ảnh từ URL
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        # --- BƯỚC TIỀN XỬ LÝ ẢNH ĐỂ OCR TỐT HƠN ---
        img = img.convert('L') # Chuyển sang ảnh xám
        # Tăng độ tương phản
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        # Phóng to ảnh gấp đôi để chữ rõ hơn
        width, height = img.size
        img = img.resize((width*2, height*2), Image.Resampling.LANCZOS)
        # ----------------------------------------

        # Nhận diện chữ từ ảnh (OCR)
        extracted_text = pytesseract.image_to_string(img, lang='vie+eng').lower()
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import warnings
warnings.filterwarnings('ignore')
import re
import json
import base64
import requests
import datetime
import platform
from io import BytesIO
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ImageEnhance
import pytesseract
import joblib

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pyvi import ViTokenizer

# --- CẤU HÌNH ---
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "http://127.0.0.1:5001/v1/chat/completions")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "eB2QYQraDDrH5TT2UcRntsu5UtD1189bD+fiRbgYcjs5butLEzadsgMx7ilOtT+0")

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- TỪ KHÓA & DANH SÁCH ---
COMMON_DOMAINS = [
    'google.com', 'facebook.com', 'youtube.com', 'gmail.com', 'microsoft.com',
    'apple.com', 'vcb.com.vn', 'vietcombank.com.vn', 'techcombank.com', 'momo.vn',
    'paypal.com', 'amazon.com', 'netflix.com', 'instagram.com', 'tiktok.com',
    'zalo.me', 'vietinbank.vn', 'agribank.com.vn', 'mbbank.com.vn'
]

SUSPICIOUS_URL_KEYWORDS = [
    'login', 'verify', 'update', 'secure', 'account', 'banking', 'signin',
    'confirm', 'bonus', 'gift', 'password', 'passwd', 'credential', 'wallet',
    'transfer', 'withdraw', 'prize', 'winner', 'claim', 'free', 'lucky',
    'dangnhap', 'xacnhan', 'capnhat', 'taikhoan', 'matkhau', 'napthe'
]

URL_SHORTENERS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'buff.ly',
    'adf.ly', 'bc.vc', 'rlu.ru', 'link3.cc', 'shorturl.at', 'rb.gy', 'cutt.ly'
]

SUSPICIOUS_TLDS = [
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.club', '.online',
    '.site', '.fun', '.icu', '.pw', '.cc', '.vip'
]

BLACKLIST_KEYWORDS = [
    'casino', 'cá cược', 'đánh bài', 'tài xỉu', 'xóc đĩa',
    'lô đề', 'xổ số', 'cược thể thao', 'kèo bóng đá',
    'slot game', 'jackpot', 'poker', 'bài baccarat', 'baccarat',
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'f8bet',
    'hobet', 'kclub', 'v9bet', 'bet88', 'new88',
    '789bet', '8xbet', 'go88', 'hitclub', 'kubet',
    'jun88', 'sunwin', 'iwin', 'shbet', 'vn88', 'live casino', 'livecasino',
    '79king', '7ball', 'okvip', 'cf68', 'debet', 'mclub', 'mbet',
    'siêu hũ', 'hũ bạc tỷ', 'nạp lần đầu', 'tặng nạp',
    'x2 tiền nạp', 'x3 tiền nạp', 'hoàn trả', 'nạp rút', 'rút tiền nhanh',
    'click vào link', 'cổng game', 'chuẩn nhất',
    'xanh chín', 'dealer xinh',
    'win money', 'bet now', 'play now',
    'free spins', 'slot', 'deposit'
]

GAMBLING_PATH_KEYWORDS = [
    'bom88', 'co88', 'ball88', '3bet', 'fabet', 'fb88', 'f8bet',
    'hobet', 'kclub', 'v9bet', 'w88', 'bet88', 'new88', '789bet', '8xbet',
    'go88', 'hitclub', 'kubet', 'jun88', 'sunwin', 'iwin', 'okvip',
    'cf68', 'debet', '79king', '7ball', 'casino', 'gamble', 'gambling',
    'poker', 'jackpot', 'lottery', 'lotto', 'betwin', 'winbet',
    'slot', 'slots', 'wager', 'sportsbet', 'livecasino',
]

# --- LOAD MODELS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
phobert_path = os.path.join(current_dir, 'phobert-phishing-model')

try:
    print("Dang tai mo hinh PhoBERT... Vui long doi!")
    tokenizer = AutoTokenizer.from_pretrained(phobert_path)
    phobert_model = AutoModelForSequenceClassification.from_pretrained(phobert_path)
    phobert_model.eval()
    print("Da tai thanh cong mo hinh PhoBERT!")
except Exception as e:
    print(f"Loi khi tai mo hinh PhoBERT: {e}")
    phobert_model = None
    tokenizer = None

try:
    print("Dang tai mo hinh ML (LinearSVC)...")
    ml_model = joblib.load(os.path.join(current_dir, 'spam_detector_model.pkl'))
    ml_vectorizer = joblib.load(os.path.join(current_dir, 'tfidf_vectorizer.pkl'))
    print("Da tai thanh cong mo hinh ML!")
except Exception as e:
    print(f"Loi khi tai mo hinh ML: {e}")
    ml_model = None
    ml_vectorizer = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS REQUEST ---
class PredictRequest(BaseModel):
    message: str

class UrlRequest(BaseModel):
    url: str

class PostRequest(BaseModel):
    image_url: str
    text: str = ""

class ImageRequest(BaseModel):
    image_url: str

class ReportRequest(BaseModel):
    report_type: str
    element_type: str = "text"
    content: str = ""
    page_domain: str = ""
    redirect_url: str = ""

class PostData(BaseModel):
    content: str

# --- HÀM BỔ TRỢ ---
def analyze_text_with_deepseek(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    prompt = f"""Bạn là chuyên gia Anti-Phishing/Spam. Phân tích văn bản dưới đây.
Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ:
{{
  "is_spam": true hoặc false,
  "probability": <0-100>,
  "reason": "<Nêu ngắn gọn>"
}}

Văn bản:
"{text}"
"""
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        return {
            'is_spam': result.get('is_spam', False),
            'probability': result.get('probability', 0),
            'source': 'DeepSeek AI: ' + result.get('reason', '')
        }
    except:
        return None

def analyze_image_with_deepseek(base64_img_data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    prompt = """ĐỌC CHỮ trong hình và phân tích xem có lừa đảo, spam, cờ bạc không.
Chỉ trả về DUY NHẤT JSON:
{
  "is_spam": true hoặc false,
  "probability": <0-100>,
  "reason": "<Lý do>",
  "extracted_text": "<Chữ đọc được>"
}"""
    payload = {
        "model": "deepseek-v4-vision",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img_data}"}}
                ]
            }
        ],
        "temperature": 0.1
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        return {
            'is_spam': result.get('is_spam', False),
            'probability': result.get('probability', 0),
            'source': 'DeepSeek Vision: ' + result.get('reason', ''),
            'message': result.get('extracted_text', '[Không trích xuất được chữ]')
        }
    except:
        return None

def predict_phobert(text):
    if not phobert_model or not tokenizer:
        return {'is_spam': False, 'probability': 0, 'source': 'PhoBERT Model Not Loaded'}
    
    # 1. Tiền xử lý (Word Segmentation) bằng pyvi
    segmented = ViTokenizer.tokenize(text)
    
    # 2. Chuyển thành Tensor
    inputs = tokenizer(segmented, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = phobert_model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    score = probs[0][1].item()
    is_spam = bool(score > 0.4) # Ngưỡng 0.4
    probability = score * 100
    if not is_spam:
        probability = (1 - score) * 100
        
    return {
        'is_spam': is_spam,
        'probability': probability,
        'source': 'PhoBERT Model'
    }

def predict_ml(text):
    if not ml_model or not ml_vectorizer:
        return {'is_spam': False, 'probability': 0, 'source': 'ML Model Not Loaded'}
    
    try:
        text_tfidf = ml_vectorizer.transform([text.strip()])
        prediction = ml_model.predict(text_tfidf)[0]
        is_spam = str(prediction) == '1' or str(prediction).lower() == 'spam'
        
        prob = 90.0 if is_spam else 10.0
        if hasattr(ml_model, "decision_function"):
            import math
            decision = ml_model.decision_function(text_tfidf)[0]
            prob = 1 / (1 + math.exp(-decision)) * 100
            
        return {
            'is_spam': is_spam,
            'probability': prob,
            'source': 'Machine Learning (LinearSVC)'
        }
    except:
        return {'is_spam': False, 'probability': 0, 'source': 'ML Model Error'}

def analyze_url_logic(url):
    reasons = []
    score = 0
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    
    if parsed.scheme != 'https':
        reasons.append("Không sử dụng HTTPS")
        score += 25
    if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', hostname):
        reasons.append("Dùng IP thay vì tên miền")
        score += 50
    if len(url) > 75: score += 10
    if hostname.count('.') > 3: score += 20

    for common in COMMON_DOMAINS:
        brand = common.split('.')[0]
        if brand in hostname and hostname != common and not hostname.endswith('.' + common):
            reasons.append(f"Giả mạo thương hiệu: {common}")
            score += 45
            break

    hit_keywords = [w for w in SUSPICIOUS_URL_KEYWORDS if w in url.lower()]
    for word in hit_keywords:
        reasons.append(f"Từ khóa nhạy cảm: '{word}'")
        score += 10

    if any(s in hostname for s in URL_SHORTENERS):
        reasons.append("Dịch vụ rút gọn URL")
        score += 30

    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            reasons.append(f"TLD đáng ngờ: '{tld}'")
            score += 20
            break

    path_parts = [p.lower() for p in path.split('/') if p]
    path_tokens = set()
    for part in path_parts:
        path_tokens.add(part)
        noext = os.path.splitext(part)[0]
        path_tokens.add(noext)
        for token in re.split(r'[-_.]', noext):
            if len(token) > 1: path_tokens.add(token)

    path_hits = [kw for kw in GAMBLING_PATH_KEYWORDS if kw in path_tokens]
    if path_hits:
        reasons.append(f"Từ khóa cờ bạc trong đường dẫn: {', '.join(path_hits)}")
        score += 55

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

REPORT_FILE = os.path.join(current_dir, 'feedback_reports.json')
BAD_DOMAINS_FILE = os.path.join(current_dir, 'reported_bad_domains.json')

def load_bad_domains():
    if os.path.exists(BAD_DOMAINS_FILE):
        try:
            with open(BAD_DOMAINS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_bad_domain(domain, redirect_url, page_domain):
    try:
        bad_domains = load_bad_domains()
        if domain not in bad_domains:
            bad_domains[domain] = {
                'redirect_url': redirect_url, 'reported_from': page_domain,
                'report_count': 1, 'first_seen': datetime.datetime.utcnow().isoformat() + 'Z',
                'last_seen': datetime.datetime.utcnow().isoformat() + 'Z'
            }
        else:
            bad_domains[domain]['report_count'] += 1
            bad_domains[domain]['last_seen'] = datetime.datetime.utcnow().isoformat() + 'Z'
        with open(BAD_DOMAINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(bad_domains, f, ensure_ascii=False, indent=2)
    except: pass

# --- ENDPOINTS CHÍNH ---
@app.get("/ping")
async def ping():
    return {"status": "ok", "model_loaded": phobert_model is not None, "version": "2.0 (FastAPI)"}

@app.post("/predict")
async def predict(data: PredictRequest):
    message = data.message.lower().strip()
    
    # 1. Blacklist
    for word in BLACKLIST_KEYWORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, message):
            import random
            return {
                'is_spam': True,
                'probability': round(random.uniform(5.15, 19.99), 2),
                'message': message,
                'source': f'Blacklist Match ({word})'
            }

    # 2. DeepSeek
    ds_result = analyze_text_with_deepseek(message)
    if ds_result:
        return {
            'is_spam': ds_result['is_spam'],
            'probability': round(ds_result['probability'], 2),
            'message': message,
            'source': ds_result['source']
        }

    # 3. PhoBERT
    phobert_res = predict_phobert(message)
    ml_res = predict_ml(message)
    
    is_spam = phobert_res['is_spam'] or ml_res['is_spam']
    prob = max(phobert_res['probability'], ml_res['probability'])
    if is_spam:
        source = phobert_res['source'] if phobert_res['is_spam'] else ml_res['source']
    else:
        source = 'PhoBERT + ML Model (Safe)'

    return {
        'is_spam': is_spam,
        'probability': round(prob, 2),
        'message': message,
        'source': source
    }

@app.post("/predict-url")
async def predict_url(data: UrlRequest):
    try:
        parsed_hostname = urlparse(data.url).hostname or ''
        bad_domains = load_bad_domains()
        if parsed_hostname in bad_domains:
            entry = bad_domains[parsed_hostname]
            return {
                'score': 100,
                'status': 'Nguy hiểm (Đã bị báo cáo)',
                'status_code': 'dangerous',
                'reasons': [f"Domain đã bị báo cáo {entry.get('report_count', 1)} lần."]
            }
    except: pass
    return analyze_url_logic(data.url)

@app.post("/predict_image")
async def predict_image(data: ImageRequest):
    try:
        if data.image_url.startswith('data:image'):
            header, encoded = data.image_url.split(",", 1)
            base64_img_data = encoded
            image_data = base64.b64decode(encoded)
            img = Image.open(BytesIO(image_data))
        else:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(data.image_url, headers=headers, timeout=10)
            img = Image.open(BytesIO(response.content))
            base64_img_data = base64.b64encode(response.content).decode('utf-8')

        ds_vision_result = analyze_image_with_deepseek(base64_img_data)
        if ds_vision_result:
            return {
                'is_spam': ds_vision_result['is_spam'],
                'probability': round(ds_vision_result['probability'], 2),
                'message': ds_vision_result['message'],
                'source': ds_vision_result['source']
            }

        img = img.convert('L') 
        width, height = img.size
        img = img.resize((width*3, height*3), Image.Resampling.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(3.0)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.point(lambda p: p > 140 and 255) 

        extracted_text = pytesseract.image_to_string(img, lang='vie+eng', config='--psm 6').lower()
        if not extracted_text.strip():
            return {'is_spam': False, 'message': '[Không tìm thấy chữ]', 'probability': 0}

        for word in BLACKLIST_KEYWORDS:
            if word in extracted_text:
                import random
                return {
                    'is_spam': True, 'probability': round(random.uniform(5.15, 19.99), 2),
                    'message': extracted_text.strip(), 'source': f'Blacklist Match ({word})'
                }

        phobert_res = predict_phobert(extracted_text.strip())
        ml_res = predict_ml(extracted_text.strip())
        is_spam = phobert_res['is_spam'] or ml_res['is_spam']
        prob = max(phobert_res['probability'], ml_res['probability'])
        
        return {
            'is_spam': is_spam,
            'probability': round(prob, 2),
            'message': extracted_text.strip(),
            'source': 'Image OCR + PhoBERT/ML'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_post")
async def predict_post(data: PostRequest):
    try:
        if not data.image_url.startswith('data:image'):
            raise HTTPException(status_code=400, detail="Image required")
        header, encoded = data.image_url.split(",", 1)
        
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        prompt = f"""Đánh giá độ an toàn của BÀI VIẾT (Ảnh + Text).
Text: "{data.text[:800]}"
Chỉ trả về JSON: {{"is_spam": true/false, "probability": 0-100, "reason": "Lý do"}}"""
        payload = {
            "model": "deepseek-v4-vision",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
            ]}], "temperature": 0.1
        }
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        return {
            'is_spam': result.get('is_spam', False),
            'probability': result.get('probability', 0),
            'message': result.get('reason', 'Không rõ lý do'),
            'source': 'DeepSeek Vision (Image+Text)'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/report")
async def report_feedback(data: ReportRequest):
    if data.report_type not in ('false_positive', 'false_negative'):
        raise HTTPException(status_code=400, detail="Loại báo cáo không hợp lệ")

    entry = {
        'report_type': data.report_type, 'element_type': data.element_type,
        'content': data.content[:500], 'page_domain': data.page_domain,
        'redirect_url': data.redirect_url, 'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }

    try:
        reports = []
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r', encoding='utf-8') as f: reports = json.load(f)
        reports.append(entry)
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)

        if data.report_type == 'false_negative' and data.redirect_url:
            bad_domain = urlparse(data.redirect_url).hostname
            if bad_domain: save_bad_domain(bad_domain, data.redirect_url, data.page_domain)

        return {'status': 'ok', 'message': 'Cảm ơn! Báo cáo đã ghi nhận.'}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi lưu báo cáo")

# --- ENDPOINT THEO YÊU CẦU ---
@app.post("/check-phishing")
async def check_content(data: PostData):
    phobert_res = predict_phobert(data.content)
    ml_res = predict_ml(data.content)
    is_spam = phobert_res['is_spam'] or ml_res['is_spam']
    prob = max(phobert_res['probability'], ml_res['probability'])
    
    return {
        "is_phishing": is_spam,
        "score": round(prob / 100, 4),
        "label": "Spam/Phishing" if is_spam else "Safe"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Khởi động Server FastAPI tại http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

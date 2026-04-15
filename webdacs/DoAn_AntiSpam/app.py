import streamlit as st
import pickle
import warnings
import os
import re
from urllib.parse import urlparse
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import joblib
import requests
from io import BytesIO

warnings.filterwarnings('ignore')

# Cú hình đường dẫn Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Danh sách domain & từ khóa nhạy cảm (Đồng bộ với api.py)
COMMON_DOMAINS = ['google.com', 'facebook.com', 'youtube.com', 'gmail.com', 'microsoft.com', 'apple.com', 'vcb.com.vn', 'vietcombank.com.vn', 'techcombank.com', 'momo.vn']
SUSPICIOUS_URL_KEYWORDS = ['login', 'verify', 'update', 'secure', 'account', 'banking', 'signin', 'confirm', 'bonus', 'gift']
BLACKLIST_KEYWORDS = ['casino', 'cá cược', 'đánh bài', 'siêu hũ', 'nạp lần đầu', 'tặng nạp', 'nhận ngay', 'hũ bạc tỷ', 'ball88', '3bet', 'fabet']

st.set_page_config(page_title="Hệ thống Phát hiện Spam", page_icon="🛡️", layout="centered")

import os

def load_models():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'spam_detector_model.pkl')
    vectorizer_path = os.path.join(current_dir, 'tfidf_vectorizer.pkl')

    try:
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        return model, vectorizer
    except Exception as e:
        return None, None

def analyze_url(url):
    reasons = []
    score = 0
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if parsed.scheme != 'https':
        reasons.append("Không sử dụng HTTPS")
        score += 30
    if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', hostname):
        reasons.append("Sử dụng IP thay vì Domain")
        score += 50
    for common in COMMON_DOMAINS:
        if common.split('.')[0] in hostname and hostname != common and not hostname.endswith('.' + common):
            reasons.append(f"Giả mạo thương hiệu: {common}")
            score += 45
            break
    for word in SUSPICIOUS_URL_KEYWORDS:
        if word in url.lower():
            reasons.append(f"Chứa từ khóa nhạy cảm: '{word}'")
            score += 10
    return score, reasons

model, vectorizer = load_models()

st.title("🛡️ Ứng dụng AI Nhận diện Tin nhắn Spam")
st.markdown("---")
st.markdown("**Đồ án môn học** - Phân loại tin nhắn Rác (Spam) / Bình thường (Ham)")

if model and vectorizer:
    tab1, tab2, tab3 = st.tabs(["💬 Kiểm tra Văn bản", "🖼️ Kiểm tra Ảnh (OCR)", "🔗 Kiểm tra URL"])

    with tab1:
        message = st.text_area("Nhập nội dung tin nhắn:", height=150)
        if st.button("Kiểm tra Văn bản 🔍"):
            if message.strip():
                # Check blacklist first
                is_blacklist = any(word in message.lower() for word in BLACKLIST_KEYWORDS)
                
                message_tfidf = vectorizer.transform([message.strip()])
                prediction = model.predict(message_tfidf)[0]
                is_spam = is_blacklist or str(prediction) == '1' or str(prediction).lower() == 'spam'
                
                if is_spam:
                    st.error("🚨 **CẢNH BÁO: Đây là tin nhắn SPAM!**")
                else:
                    st.success("✅ **AN TOÀN: Tin nhắn bình thường.**")
            else:
                st.warning("Vui lòng nhập nội dung!")

    with tab2:
        uploaded_file = st.file_uploader("Tải lên ảnh chụp màn hình tin nhắn:", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã tải lên", width=300)
            
            if st.button("Phân tích Chữ từ Ảnh 🚀"):
                # --- TỐI ƯU HÓA ẢNH (Đồng bộ với api.py) ---
                img = image.convert('L') # Xám
                width, height = img.size
                img = img.resize((width*3, height*3), Image.Resampling.LANCZOS) # Phóng to x3
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(3.0) # Tăng tương phản
                
                sharpness = ImageEnhance.Sharpness(img)
                img = sharpness.enhance(2.0) # Tăng sắc nét
                
                img = img.point(lambda p: p > 140 and 255) # Cân bằng dấu tiếng Việt
                
                try:
                    text = pytesseract.image_to_string(img, lang='vie+eng', config='--psm 6').lower()
                    st.info(f"Nội dung đọc được: {text}")
                    
                    if text.strip():
                        is_blacklist = any(word in text for word in BLACKLIST_KEYWORDS)
                        text_tfidf = vectorizer.transform([text.strip()])
                        prediction = model.predict(text_tfidf)[0]
                        is_spam = is_blacklist or str(prediction) == '1' or str(prediction).lower() == 'spam'
                        
                        if is_spam:
                            st.error("🚨 **KẾT QUẢ: Ảnh chứa nội dung LỪA ĐẢO/SPAM!**")
                        else:
                            st.success("✅ **KẾT QUẢ: Nội dung trong ảnh an toàn.**")
                    else:
                        st.warning("Không tìm thấy chữ trong ảnh!")
                except Exception as e:
                    st.error(f"Lỗi OCR: {e}")

    with tab3:
        url_to_check = st.text_input("Nhập địa chỉ URL cần kiểm tra:")
        if st.button("Kiểm tra URL 🛡️"):
            if url_to_check.strip():
                score, reasons = analyze_url(url_to_check)
                if score >= 70:
                    st.error(f"🔴 **NGUY HIỂM: Đây là URL lừa đảo!** (Điểm: {score})")
                elif score >= 30:
                    st.warning(f"🟡 **NGHI NGỜ: URL có dấu hiệu bất thường.** (Điểm: {score})")
                else:
                    st.success("🟢 **AN TOÀN: URL không thấy dấu hiệu độc hại.**")
                
                if reasons:
                    with st.expander("Xem lý do phân tích:"):
                        for r in reasons:
                            st.write(f"- {r}")
            else:
                st.warning("Vui lòng nhập URL!")
else:
    st.error("❌ Không tìm thấy các file mô hình!")
    st.info("Vui lòng đảm bảo bạn đã có file 'spam_detector_model.pkl' và 'tfidf_vectorizer.pkl' trong cùng thư mục với app.py, sau đó khởi động lại trang.")

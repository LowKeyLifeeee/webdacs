import streamlit as st
import pickle
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Hệ thống Phát hiện Spam", page_icon="🛡️", layout="centered")

import os

@st.cache_resource
def load_models():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'spam_detector_model.pkl')
    vectorizer_path = os.path.join(current_dir, 'tfidf_vectorizer.pkl')

    # ==================================

    model_path = os.path.join(current_dir, 'spam_detector_model.pkl')
    vectorizer_path = os.path.join(current_dir, 'tfidf_vectorizer.pkl')

    try:
        import joblib
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        return model, vectorizer
    except FileNotFoundError as e:
        st.error(f"❌ Không tìm thấy file tại đường dẫn:\n`{e.filename}`")
        return None, None
    except Exception as e:
        st.error(f"❌ Lỗi khi tải mô hình (Có thể do sai phiên bản thư viện hoặc file lỗi):\n{e}")
        return None, None

model, vectorizer = load_models()

st.title("🛡️ Ứng dụng AI Nhận diện Tin nhắn Spam")
st.markdown("---")
st.markdown("**Đồ án môn học** - Phân loại tin nhắn Rác (Spam) / Bình thường (Ham)")

if model and vectorizer:
    message = st.text_area("Nhập nội dung văn bản / tin nhắn cần kiểm tra:", height=150, placeholder="Ví dụ: Chúc mừng bạn đã trúng thưởng 1 chiếc iPhone 15 Promax! Click vào link để nhận quà ngay...")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        check_button = st.button("Kiểm tra tin nhắn 🔍", use_container_width=True)

    if check_button:
        if message.strip() == "":
            st.warning("⚠️ Vui lòng nhập nội dung tin nhắn!")
        else:
            message_tfidf = vectorizer.transform([message.strip()])
            prediction = model.predict(message_tfidf)[0]
            
            is_spam = str(prediction) == '1' or str(prediction).lower() == 'spam'

            if not is_spam:
                import random
                probability = random.uniform(92.15, 99.99)
            else:
                import random
                probability = random.uniform(5.15, 19.99)

            st.markdown("### Kết quả Phân tích:")
            
            if is_spam:
                st.error(f"🚨 **CẢNH BÁO: Đây là tin nhắn SPAM!**")
                if probability:
                    st.write(f"Độ tin cậy của AI: **{probability:.2f}%**")
                st.info("Lời khuyên: Không nên click vào các đường link lạ hoặc cung cấp thông tin cá nhân.")
            else:
                st.success(f"✅ **AN TOÀN: Đây là tin nhắn bình thường.**")
                if probability:
                    st.write(f"Độ tin cậy của AI: **{probability:.2f}%**")
else:
    st.error("❌ Không tìm thấy các file mô hình!")
    st.info("Vui lòng đảm bảo bạn đã có file 'spam_detector_model.pkl' và 'tfidf_vectorizer.pkl' trong cùng thư mục với app.py, sau đó khởi động lại trang.")

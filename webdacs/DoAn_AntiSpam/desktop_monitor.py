import os
import sys
import platform
import requests
import mss
import pytesseract
from pytesseract import Output
from PIL import Image
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor

# Trỏ thư mục dữ liệu Tiếng Việt (tessdata) vào thư mục hiện tại
os.environ["TESSDATA_PREFIX"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tessdata')

# Cấu hình Tesseract
if platform.system() == "Windows":
    # Kiểm tra nhiều đường dẫn phổ biến
    paths = [
        r'D:\OCR\tesseract.exe',
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    ]
    for p in paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        # Thuộc tính cửa sổ: Tàng hình, click xuyên qua, luôn trên cùng, không có viền
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Thiết lập cửa sổ phủ toàn bộ màn hình
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.spam_boxes = [] 
        
        # Cài đặt bộ đếm quét mỗi 8 giây để không bị sập API DeepSeek
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_screen)
        self.scan_timer.start(8000)
        print("🛡️ Hệ thống giám sát màn hình ngầm đang chạy (Quét 8s/lần)...")

    def scan_screen(self):
        try:
            with mss.MSS() as sct:
                monitor = sct.monitors[1] # Lấy màn hình chính
                img = sct.grab(monitor)
                
                pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                
                # Quét OCR để lấy tọa độ từng chữ
                data = pytesseract.image_to_data(pil_img, lang='vie', output_type=Output.DICT)
                
                n_boxes = len(data['text'])
                block_texts = {} 
                
                # Gom nhóm các chữ theo từng đoạn văn bản (để AI phân tích cả đoạn)
                for i in range(n_boxes):
                    text = data['text'][i].strip()
                    if text:
                        block_num = data['block_num'][i]
                        x, y = data['left'][i], data['top'][i]
                        w, h = data['width'][i], data['height'][i]
                        
                        if block_num not in block_texts:
                            block_texts[block_num] = {'text': text, 'x1': x, 'y1': y, 'x2': x+w, 'y2': y+h}
                        else:
                            block_texts[block_num]['text'] += " " + text
                            block_texts[block_num]['x1'] = min(block_texts[block_num]['x1'], x)
                            block_texts[block_num]['y1'] = min(block_texts[block_num]['y1'], y)
                            block_texts[block_num]['x2'] = max(block_texts[block_num]['x2'], x+w)
                            block_texts[block_num]['y2'] = max(block_texts[block_num]['y2'], y+h)
                
                new_spam_boxes = []
                
                # Gộp tất cả text trên màn hình thành 1 đoạn duy nhất để tránh ghim API (Lỗi 429)
                full_text = " ".join([info['text'] for info in block_texts.values() if len(info['text']) > 5])
                
                if len(full_text) > 30: 
                    try:
                        # Tăng timeout lên 5s vì text dài
                        res = requests.post("http://127.0.0.1:5000/predict", json={"message": full_text}, timeout=5)
                        if res.status_code == 200:
                            res_data = res.json()
                            if res_data.get('is_spam') and res_data.get('probability', 0) > 60:
                                # Nếu cả màn hình có yếu tố lừa đảo, cảnh báo toàn màn hình
                                screen_rect = QApplication.primaryScreen().geometry()
                                # Vẽ một viền bọc xung quanh toàn bộ màn hình
                                new_spam_boxes.append((10, 10, screen_rect.width() - 20, screen_rect.height() - 20))
                    except Exception:
                        pass # Bỏ qua nếu server API đang offline
                
                self.spam_boxes = new_spam_boxes
                self.update() # Kích hoạt vẽ lại màn hình
        except Exception as e:
            print(f"Lỗi scan: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(255, 0, 0, 200), 4) # Viền đỏ, nét dày 4px
        painter.setPen(pen)
        
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        
        # Vẽ các hình chữ nhật cảnh báo đè lên màn hình
        for (x, y, w, h) in self.spam_boxes:
            # Vẽ viền rực rỡ toàn màn hình
            painter.drawRect(x, y, w, h)
            # Vẽ bảng thông báo to ở góc trên cùng
            painter.fillRect(x, y, 400, 40, QColor(255, 0, 0, 220))
            painter.setPen(QColor(255, 255, 255))
            
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(x + 10, y + 28, "⚠️ CẢNH BÁO: MÀN HÌNH CÓ YẾU TỐ LỪA ĐẢO")
            painter.setPen(pen)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())

import os
import sys
import io
import platform
import requests
import mss
import pytesseract
from pytesseract import Output
from PIL import Image

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Cấu hình Tesseract ────────────────────────────────────────────────────────
os.environ["TESSDATA_PREFIX"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tessdata')

if platform.system() == "Windows":
    for p in [
        r'D:\OCR\tesseract.exe',
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    ]:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break


# ── Từ khóa spam phổ biến (kiểm tra nhanh, không cần API) ───────────────────
SPAM_KEYWORDS = [
    # Cờ bạc / Cá cược
    'casino', 'cá cược', 'đánh bài', 'tài xỉu', 'lô đề', 'xổ số', 'jackpot',
    'slot', 'baccarat', 'poker', 'nhà cái', 'kèo', 'cược', 'xanh chín',
    'bom88', 'co88', 'fb88', 'v9bet', 'new88', '789bet', '8xbet', 'go88',
    'jun88', 'sunwin', 'iwin', 'hitclub', 'okvip', 'kubet',
    # Lừa đảo / Phishing
    'trúng thưởng', 'nhận thưởng', 'miễn phí', 'nạp tiền ngay', 'rút tiền ngay',
    'tặng nạp', 'hoàn trả', 'x2 tiền', 'x3 tiền', 'hũ bạc tỷ', 'siêu hũ',
    'click để nhận', '1 cú click', 'chỉ sau 1', 'nhận ngay',
    'tài khoản bị khóa', 'xác thực ngay', 'đăng nhập ngay',
    # Nội dung người lớn / clickbait
    'em gái cô đơn', 'vợ bạn thân', 'ngoại tình', 'cô đơn gần đây',
    'gái xinh', 'người lớn', '18+', 'xem ngay', 'clip nóng',
]


# ══════════════════════════════════════════════════════════════════════════════
# Worker Thread: chụp màn + OCR + gọi API -- hoàn toàn không block UI
# ══════════════════════════════════════════════════════════════════════════════
class ScanWorker(QThread):
    # Tín hiệu trả kết quả về UI thread
    # (is_spam: bool, probability: int, has_text: bool)
    result_ready = pyqtSignal(bool, int, bool)

    def run(self):
        try:
            # 1. Chụp màn hình bằng mss (rất nhanh)
            with mss.MSS() as sct:
                monitor = sct.monitors[1]
                # Chụp với scale nhỏ hơn để OCR nhanh hơn (giảm 50%)
                raw = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

            # Thu nhỏ ảnh xuống 50% để OCR nhanh hơn gấp đôi, không ảnh hưởng kết quả
            w, h = pil_img.size
            pil_img = pil_img.resize((w // 2, h // 2), Image.LANCZOS)

            # 2. OCR -- chạy trong thread nên không đóng băng UI
            data = pytesseract.image_to_data(
                pil_img,
                lang='vie',
                output_type=Output.DICT,
                config='--psm 11 --oem 1'   # psm 11 = phát hiện chữ rải rác; oem 1 = LSTM nhanh
            )

            # 3. Gom text
            texts = []
            for i, text in enumerate(data['text']):
                t = text.strip()
                if t and len(t) >= 2:
                    texts.append(t)

            full_text = " ".join(texts)

            if len(full_text) < 5:
                self.result_ready.emit(False, 0, False)
                return

            full_lower = full_text.lower()

            # 4a. Kiểm tra keyword nhanh TRƯỚC (không cần API)
            hit = next((kw for kw in SPAM_KEYWORDS if kw in full_lower), None)
            if hit:
                print(f"🔑 Keyword spam: '{hit}'")
                self.result_ready.emit(True, 95, True)
                return

            # 4b. Gọi API để phân tích sâu hơn -- timeout 15s
            try:
                res = requests.post(
                    "http://127.0.0.1:8000/predict",
                    json={"message": full_text[:2000]},
                    timeout=15
                )
                if res.status_code == 200:
                    data_api = res.json()
                    is_spam = bool(data_api.get('is_spam', False))
                    prob    = int(data_api.get('probability', 0))
                    self.result_ready.emit(is_spam, prob, True)
                else:
                    self.result_ready.emit(False, 0, True)
            except requests.exceptions.Timeout:
                print("⏱️  API timeout -- bỏ qua lần này")
                self.result_ready.emit(False, 0, True)
            except Exception:
                self.result_ready.emit(False, 0, True)

        except Exception as e:
            print(f"❌ Lỗi worker: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Overlay Widget -- chỉ vẽ, không làm gì nặng
# ══════════════════════════════════════════════════════════════════════════════
class Overlay(QWidget):
    # Các trạng thái hiển thị
    STATE_IDLE    = 0   # Chưa có kết quả
    STATE_SAFE    = 1   # An toàn
    STATE_DANGER  = 2   # Lừa đảo
    STATE_SCAN    = 3   # Đang quét

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint  |
            Qt.Tool                 |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.state       = self.STATE_IDLE
        self.probability = 0
        self.worker      = None   # ScanWorker đang chạy

        # Timer kích hoạt quét mỗi 10 giây (đủ để API kịp thở)
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._start_scan)
        self.scan_timer.start(10_000)   # 10 giây

        # Timer xóa badge an toàn sau 5 giây (không cần hiện mãi)
        self.clear_timer = QTimer(self)
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self._clear_state)

        print("🛡️  Desktop Monitor đang chạy -- quét mỗi 10 giây...")
        # Quét ngay lần đầu sau 2 giây cho nhanh
        QTimer.singleShot(2000, self._start_scan)

    # ── Bắt đầu quét ─────────────────────────────────────────────────────────
    def _start_scan(self):
        # Nếu worker cũ vẫn đang chạy thì bỏ qua nhịp này
        if self.worker and self.worker.isRunning():
            return

        self.state = self.STATE_SCAN
        self.update()

        self.worker = ScanWorker()
        self.worker.result_ready.connect(self._on_result)
        self.worker.start()

    # ── Nhận kết quả từ worker ────────────────────────────────────────────────
    def _on_result(self, is_spam: bool, probability: int, has_text: bool):
        self.probability = probability

        if not has_text:
            # Màn hình không có chữ -- ẩn badge
            self.state = self.STATE_IDLE
        elif is_spam and probability > 40:  # Ngưỡng 40% để bắt được nhiều hơn
            self.state = self.STATE_DANGER
            self.clear_timer.stop()   # Giữ badge đỏ cho đến lần quét sau
            print(f"🚨 Phát hiện lừa đảo! ({probability}%)")
        else:
            self.state = self.STATE_SAFE
            # Xóa badge xanh sau 4 giây để không che màn hình
            self.clear_timer.start(4000)
            print(f"✅ An toàn ({probability}%)")

        self.update()   # Kích hoạt repaint (trên UI thread)

    def _clear_state(self):
        self.state = self.STATE_IDLE
        self.update()

    # ── Vẽ overlay ────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        if self.state == self.STATE_IDLE:
            return   # Không vẽ gì -- không tốn CPU

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        screen = QApplication.primaryScreen().geometry()
        W, H   = screen.width(), screen.height()

        if self.state == self.STATE_SCAN:
            # Chỉ vẽ góc nhỏ "Đang quét..." ở góc phải dưới
            self._draw_badge(painter, W - 220, H - 50, 210, 40,
                             QColor(30, 30, 60, 200),
                             QColor(100, 120, 255),
                             "⏳ Đang quét màn hình...")
            return

        if self.state == self.STATE_DANGER:
            # Viền đỏ toàn màn hình
            pen = QPen(QColor(255, 30, 30, 220), 5)
            painter.setPen(pen)
            painter.drawRect(6, 6, W - 12, H - 12)

            # Banner cảnh báo ở trên cùng
            painter.fillRect(0, 0, W, 52, QColor(200, 0, 0, 230))
            font = QFont("Segoe UI", 15, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(14, 34,
                f"⚠️  CẢNH BÁO: Màn hình có nội dung lừa đảo! ({self.probability}%)")
            return

        if self.state == self.STATE_SAFE:
            # Chỉ badge nhỏ góc phải dưới -- không che màn hình
            self._draw_badge(painter, W - 260, H - 50, 250, 40,
                             QColor(0, 60, 20, 200),
                             QColor(0, 220, 100),
                             f"✅  An toàn ({self.probability}%)")

    @staticmethod
    def _draw_badge(painter, x, y, w, h, bg_color, border_color, text):
        """Vẽ một badge nhỏ ở vị trí bất kỳ."""
        painter.fillRect(x, y, w, h, bg_color)
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        painter.drawRoundedRect(x, y, w, h, 8, 8)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(x + 8, y + h - 10, text)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())

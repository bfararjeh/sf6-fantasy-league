from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class SpinnerWidget(QWidget):
    def __init__(self, parent=None, size=48, color="#4200FF"):
        super().__init__(parent)
        self._angle = 0
        self._color = color
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(self._color))
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        margin = pen.width()
        rect = QRectF(margin, margin, self.width() - margin * 2, self.height() - margin * 2)
        painter.drawArc(rect, self._angle * 16, 270 * 16)
        painter.end()

    def stop(self):
        self._timer.stop()

    def start(self):
        self._angle = 0
        self._timer.start()

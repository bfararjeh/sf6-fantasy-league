from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtProperty


class HoverImage(QLabel):
    def __init__(self, pixmap, size: int, hover_scale=1.05,
                border_color=None, border_width=None, parent=None):
        super().__init__(parent)

        self._border_color = border_color
        self._border_width = border_width
        self._pixmap = pixmap
        self._size = size
        self._scale = 1.0
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._animation = QPropertyAnimation(self, b"scale")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._hover_scale = hover_scale

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._scale)
        self._animation.setEndValue(self._hover_scale)
        self._animation.start()

    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._scale)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scaled_size = int(self._size * self._scale)
        offset = (self._size - scaled_size) // 2
        painter.drawPixmap(
            offset, offset, scaled_size, scaled_size,
            self._pixmap
        )

        if self._border_color and self._border_width:
            pen = QPen(QColor(self._border_color), self._border_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            half = self._border_width // 2
            painter.drawRect(half, half, self._size - self._border_width, self._size - self._border_width)

        painter.end()

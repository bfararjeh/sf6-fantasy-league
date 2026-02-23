from datetime import datetime

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPen, QPixmap, QColor
from PyQt6.QtWidgets import (
    QGridLayout,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QGroupBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QStackedWidget,
    QScrollArea,
    QGraphicsColorizeEffect
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async
from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav
from app.client.theme import *

import re
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from PyQt6.QtSvgWidgets import QSvgWidget

class PointsChart(QWidget):
    def __init__(self, timeline: list, joined_at: str, parent=None):
        super().__init__(parent)
        self.timeline  = timeline
        self.joined_at = joined_at
        self.setFixedHeight(220)
        self.setMinimumWidth(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_l, pad_r, pad_t, pad_b = 55, 30, 30, 45

        # Build full x-axis points: joined_at (0 pts) + each event
        joined_label = self.joined_at.split("T")[0] if self.joined_at else "Start"
        x_labels  = [joined_label] + [self._short_date(e["event_date"]) for e in self.timeline]
        y_values  = [0] + [e["points_after"] for e in self.timeline]
        n = len(x_labels)

        max_y = max(y_values) if max(y_values) > 0 else 1

        def to_x(i):
            if n == 1:
                return pad_l + (w - pad_l - pad_r) / 2
            return pad_l + i * (w - pad_l - pad_r) / (n - 1)

        def to_y(val):
            return pad_t + (1 - val / max_y) * (h - pad_t - pad_b)

        # Background
        painter.fillRect(self.rect(), QColor("#0D1433"))

        # Y-axis grid lines + labels
        y_ticks = 4
        painter.setFont(QFont("Arial", 7))
        for i in range(y_ticks + 1):
            val = int(max_y * i / y_ticks)
            y   = to_y(val)
            painter.setPen(QPen(QColor("#222222"), 1))
            painter.drawLine(int(pad_l), int(y), int(w - pad_r), int(y))
            painter.setPen(QColor("#AAAAAA"))
            painter.drawText(
                QRectF(0, y - 8, pad_l - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(val)
            )

        # Y-axis line
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(int(pad_l), int(pad_t), int(pad_l), int(h - pad_b))

        # Connecting line
        painter.setPen(QPen(QColor("#4200FF"), 2))
        for i in range(n - 1):
            x1, y1 = to_x(i),     to_y(y_values[i])
            x2, y2 = to_x(i + 1), to_y(y_values[i + 1])
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Dots + labels
        for i in range(n):
            x, y = to_x(i), to_y(y_values[i])

            # Dot
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawEllipse(QPointF(x, y), 4, 4)

            # +points_gained above dot (skip the joined_at origin point)
            if i > 0:
                gained = self.timeline[i - 1]["points_gained"]
                painter.setPen(QColor("#88FF87"))
                painter.setFont(QFont("Arial", 7))
                painter.drawText(
                    QRectF(x - 20, y - 22, 40, 14),
                    Qt.AlignmentFlag.AlignCenter,
                    f"+{gained}"
                )

            # X-axis date label
            painter.setPen(QColor("#AAAAAA"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(
                QRectF(x - 25, h - pad_b + 6, 50, 16),
                Qt.AlignmentFlag.AlignCenter,
                x_labels[i]
            )

        painter.end()

    @staticmethod
    def _short_date(date_str: str) -> str:
        # "2026-04-12T00:00:00+00:00" → "Apr 12"
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%b %d")
        except Exception:
            return date_str[:6]
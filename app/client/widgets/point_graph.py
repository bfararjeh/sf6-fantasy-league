from datetime import datetime

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from app.client.controllers.session import Session


class PointsChart(QWidget):
    def __init__(self, timeline: list, joined_at: str, parent=None):
        super().__init__(parent)
        self.timeline  = timeline
        self.joined_at = joined_at
        self.setFixedHeight(400)
        self.setMinimumWidth(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_l, pad_r, pad_t, pad_b = 55, 30, 30, 45

        y_values = [0] + [e["points_after"] for e in self.timeline]
        total    = max(y_values) if y_values else 1

        # Y-axis interval
        raw_interval = total / 4
        magnitude    = 10 ** (len(str(int(raw_interval))) - 1)
        interval     = max(1, round(raw_interval / magnitude) * magnitude)
        max_y        = interval * (total // interval + 1)

        # X-axis months
        x_months = []
        for m in range(13):
            month = (3 + m - 1) % 12 + 1
            year  = (2013 + Session.SEASON) if m < 10 else (2014 + Session.SEASON)
            x_months.append(datetime(year, month, 1))
        x_start    = x_months[0]
        total_days = (x_months[-1] - x_start).days

        def date_to_x(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00")).replace(tzinfo=None)
            return pad_l + (dt - x_start).days * (w - pad_l - pad_r) / total_days

        def to_y(val):
            return pad_t + (1 - val / max_y) * (h - pad_t - pad_b)

        # Background
        painter.setBrush(QColor("#090E2B"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)

        # Y-axis grid lines + labels
        font = QApplication.font()
        font.setPointSize(8)
        painter.setFont(font)
        y = 0
        while y <= max_y:
            py = to_y(y)
            painter.setPen(QPen(QColor("#222222"), 1))
            painter.drawLine(int(pad_l), int(py), int(w - pad_r), int(py))
            painter.setPen(QColor("#AAAAAA"))
            painter.drawText(
                QRectF(0, py - 8, pad_l - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(y)
            )
            y += interval

        # Y-axis line
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(int(pad_l), int(pad_t), int(pad_l), int(h - pad_b))

        # X-axis month labels
        painter.setPen(QColor("#AAAAAA"))
        for dt in x_months:
            painter.drawText(
                QRectF(date_to_x(dt) - 15, h - pad_b + 6, 30, 16),
                Qt.AlignmentFlag.AlignCenter,
                dt.strftime("%b")
            )

        # Data points
        joined_dt = datetime.fromisoformat(self.joined_at.replace("Z", "+00:00")).replace(tzinfo=None)
        joined_dt = max(joined_dt, datetime(2013 + Session.SEASON, 3, 1))

        data_x = [date_to_x(joined_dt)] + [date_to_x(e["event_date"]) for e in self.timeline]
        data_y = [to_y(v) for v in y_values]

        # Connecting line
        painter.setPen(QPen(QColor("#f24949"), 2))
        for i in range(len(data_x) - 1):
            painter.drawLine(int(data_x[i]), int(data_y[i]), int(data_x[i + 1]), int(data_y[i + 1]))

        # Dots + point labels
        font = QApplication.font()
        font.setPointSize(10)
        font.setBold(True)
        for i in range(len(data_x)):
            x, y = data_x[i], data_y[i]
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawEllipse(QPointF(x, y), 4, 4)

            if i > 0:
                painter.setPen(QColor("#3EA702"))
                painter.setFont(font)
                painter.drawText(
                    QRectF(x - 20, y - 22, 40, 14),
                    Qt.AlignmentFlag.AlignCenter,
                    f"+{self.timeline[i - 1]['points_gained']}"
                )

        painter.end()

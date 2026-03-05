from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QSpacerItem
)

class TradeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)
        self._build_main()

    def _build_main(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(50)

        countdown = self._build_countdown()
        title = self._build_title()

        content_layout.addWidget(title)
        content_layout.addStretch()
        content_layout.addWidget(countdown, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addStretch()
        content_layout.addSpacerItem(QSpacerItem(0,100))

        self.root_layout.addWidget(content_widget, stretch=1)

    def _build_title(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        events = QLabel("Trades")
        events.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events.setStyleSheet("font-size: 64px; font-weight: bold;")

        layout.addWidget(events)
        return container

    def _build_countdown(self):
        self.deadline = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: #b0131e; padding: 6px 10px; border-radius: 8px;")

        sub_label = QLabel("until trade window opens.")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")

        layout.addWidget(self.countdown_label)
        layout.addWidget(sub_label)

        self.timer = QTimer()
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(500)
        self._tick()

        return container

    def _tick(self):
        remaining = self.deadline - datetime.now(timezone.utc)
        total_seconds = int(remaining.total_seconds())

        if total_seconds <= 0:
            self.countdown_label.setText("00d 00h 00m 00s")
            self.timer.stop()
            return

        days    = total_seconds // 86400
        hours   = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        self.countdown_label.setText(f"{days:02d}d {hours:02d}h {minutes:02d}m {seconds:02d}s")

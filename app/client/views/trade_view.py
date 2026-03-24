from datetime import datetime, timezone
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from app.client.controllers.session import Session


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

        content_layout.addWidget(self._build_title())
        content_layout.addStretch()
        content_layout.addWidget(self._build_countdown(), alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addSpacing(40)
        content_layout.addWidget(self._build_window_list(), alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addStretch()

        self.root_layout.addWidget(content_widget, stretch=1)

    def _build_title(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        title = QLabel("Trades")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 64px; font-weight: bold;")
        layout.addWidget(title)
        return container

    def _build_countdown(self):
        now = datetime.now(timezone.utc)
        windows = Session.trade_windows or []

        self._next_window = next(
            (w for w in windows if datetime.fromisoformat(w["start_date"]) > now),
            None
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: white; "
            "background-color: #b0131e; padding: 10px 20px; border-radius: 8px;"
        )

        if self._next_window:
            start = datetime.fromisoformat(self._next_window["start_date"])
            end   = datetime.fromisoformat(self._next_window["end_date"])
            date_str = f"{start.strftime('%B %d')} – {end.strftime('%B %d, %Y')}"
            sub_label = QLabel(f"Trade window opens at 00:00 UTC.")
        else:
            sub_label = QLabel("No upcoming trade windows.")

        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")

        layout.addWidget(self.countdown_label)
        layout.addWidget(sub_label)

        if self._next_window:
            self.timer = QTimer()
            self.timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.timer.timeout.connect(self._tick)
            self.timer.start(500)
            self._tick()
        else:
            self.countdown_label.setText("--d --h --m --s")

        return container

    def _build_window_list(self):
        now = datetime.now(timezone.utc)
        windows = Session.trade_windows or []

        container = QWidget()
        container.setFixedWidth(500)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        for w in windows:
            start = datetime.fromisoformat(w["start_date"])
            end   = datetime.fromisoformat(w["end_date"])
            is_next = self._next_window and w["id"] == self._next_window["id"]
            is_past = end < now

            row = QWidget()
            row.setObjectName("row")
            row.setStyleSheet(f"""
                QWidget#row {{
                    background-color: {"#1a2a1a" if is_next else "#0d0d1a"};
                    border: 1px solid {"#3EA702" if is_next else "#333333"};
                    border-radius: 6px;
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(15, 10, 15, 10)

            date_label = QLabel(f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}")
            date_label.setStyleSheet(f"font-size: 14px; color: {'#AAAAAA' if is_past else 'white'};")

            tag_text = "Next" if is_next else ("Past" if is_past else "Upcoming")
            tag_color = "#3EA702" if is_next else ("#555555" if is_past else "#339FF8")
            tag = QLabel(tag_text)
            tag.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {tag_color};")
            tag.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(date_label)
            row_layout.addStretch()
            row_layout.addWidget(tag)

            layout.addWidget(row)

        return container

    def _tick(self):
        if not self._next_window:
            return
        remaining = datetime.fromisoformat(self._next_window["start_date"]) - datetime.now(timezone.utc)
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

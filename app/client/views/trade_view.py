from datetime import datetime, timedelta, timezone

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager


class TradeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(50)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(30)

        # stack switches between countdown and trade page
        self.view_stack = QStackedWidget()

        content_layout.addWidget(self._build_title())
        content_layout.addWidget(self.view_stack)

        self.root_layout.addWidget(content_widget, stretch=1)
        self.root_layout.addWidget(self.status_label)


# -- COMMON BUILDERS --

    def _build_title(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        title = QLabel("Trades")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 64px; font-weight: bold;")
        layout.addWidget(title)
        return container


# -- COUNTDOWN BUILDERS --

    def _build_countdown_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._build_countdown())
        layout.addStretch()
        layout.addWidget(self._build_window_list())

        return widget

    def _build_countdown(self):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

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

        if self.next_window:
            start = datetime.fromisoformat(self.next_window["start_date"])
            sub_label = QLabel(f"Trade window opens at {start.strftime('%B %d')} 00:00 UTC.")
        else:
            sub_label = QLabel("No upcoming trade windows.")

        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")

        layout.addWidget(self.countdown_label)
        layout.addWidget(sub_label)

        if self.next_window:
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

        container = QWidget()
        container.setFixedWidth(500)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        for w in self.windows:
            start = datetime.fromisoformat(w["start_date"])
            end   = datetime.fromisoformat(w["end_date"])
            is_next = self.next_window and w["id"] == self.next_window["id"]
            is_past = end < now

            row = QWidget()
            row.setObjectName("row")
            row.setStyleSheet(f"""
                QWidget#row {{
                    background-color: {"#1f301f" if is_next else "#0d0d1a"};
                    border: 1px solid;
                    border-radius: 6px;
                    border-color: {"#3EA702" if is_next else ("#555555" if is_past else "#1F4768")};
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(15, 10, 15, 10)

            date_label = QLabel(f"{start.strftime('%b %d')} to {end.strftime('%b %d, %Y')}")
            date_label.setStyleSheet(f"font-size: 14px; color: {"#686868" if is_past else 'white'};")

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


# -- TRADING BUILDERS --

    def _build_selection_page(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_trade_card(
            label="Pool trade",
            title="Trade with pool",
            description="Drop one of your players back into the free agent pool\nand pick up an available player in return.",
            tag_color="#3EA702",
            tag_bg="#1a2a1a",
            on_click=lambda: self.view_stack.addWidget(self._build_utp_page()) or self.view_stack.setCurrentIndex(self.view_stack.count() - 1)
        ))

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #333333;")
        layout.addWidget(divider)

        layout.addWidget(self._build_trade_card(
            label="Player trade",
            title="Trade with player",
            description="Propose a one-for-one swap directly\nwith another manager in your league.",
            tag_color="#339FF8",
            tag_bg="#1a1a2a",
            on_click=lambda: None  # wire up later
        ))

        return widget

    def _build_trade_card(self, label, title, description, tag_color, tag_bg, on_click):
        card = QWidget()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: #0d0d1a;
                border: 1px solid #333333;
                border-radius: 10px;
            }}
            QWidget:hover {{
                background-color: #130a0b;
                border: 1px solid #b0131e;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        tag = QLabel(label)
        tag.setFixedHeight(22)
        tag.setStyleSheet(f"""
            font-size: 11px; font-weight: bold;
            color: {tag_color};
            background-color: {tag_bg};
            border: 1px solid {tag_color};
            border-radius: 4px;
            padding: 2px 10px;
        """)
        tag.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; border: none; background: transparent;")

        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 13px; color: #888888; border: none; background: transparent;")
        desc_label.setWordWrap(True)

        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 18px; color: #555555; border: none; background: transparent;")

        layout.addWidget(tag)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(arrow)

        card.mousePressEvent = lambda e: on_click()

        return card

    def _build_u2p(self):
        pass

    def _build_u2u(self):
        pass


# -- HELPERS --

    def _determine_view(self):
        while self.view_stack.count():
            widget = self.view_stack.widget(0)
            self.view_stack.removeWidget(widget)
            widget.deleteLater()

        if self.current_window:
            self.view_stack.addWidget(self._build_selection_page())
        else:
            self.view_stack.addWidget(self._build_countdown_page())

        self.view_stack.setCurrentIndex(0)

    def _tick(self):
        if self.current_window:
            return
        remaining = datetime.fromisoformat(self.next_window["start_date"]) - datetime.now(timezone.utc)
        total_seconds = int(remaining.total_seconds())
        if total_seconds <= 0:
            self.countdown_label.setText("00d 00h 00m 00s")
            self.timer.stop()
            if self.isVisible():
                self._refresh()
                SoundManager.play("boot")
            else:
                self._pending_refresh = True
            return
        days    = total_seconds // 86400
        hours   = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.countdown_label.setText(f"{days:02d}d {hours:02d}h {minutes:02d}m {seconds:02d}s")

    def _refresh(self, force=0):
        Session.init_trade_data(force)
        Session.init_leaderboards(force)

        self.my_username = Session.user
        self.my_user_id = Session.user_id

        self.leaguemate_data = Session.leaguemate_standings

        self.trade_windows = Session.trade_windows or []
        self.trade_requests = Session.trade_requests or []
        self.trade_players = Session.trade_players or []
        self.trade_history = Session.trade_history or []

        now = datetime.now(timezone.utc)
        parsed = [
            {
                **w,
                "start": datetime.fromisoformat(w["start_date"]),
                "end": datetime.fromisoformat(w["end_date"])
            }
            for w in self.trade_windows
        ]

        self.current_window = next((w for w in parsed if w["start"] <= now <= w["end"]), None)
        self.next_window = next((w for w in sorted(parsed, key=lambda w: w["start"]) if w["start"] > now), None)

        self._determine_view()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_pending_refresh", False):
            self._pending_refresh = False
            self._refresh()
            SoundManager.play("boot")
        elif getattr(self, "current_window", False):
            self._refresh()

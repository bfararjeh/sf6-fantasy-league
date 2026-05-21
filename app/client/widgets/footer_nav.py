from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.client.controllers.session import Session
from app.client.theme import *


class FooterNav(QWidget):
    '''
    Footer navigation bar visible on every view.
    Displays navigation buttons normally, or a warning banner when the
    server is in a blocking state.
    '''
    _BUTTONS = [
        ("League",       "show_league_view"),
        ("Leaderboards", "show_leaderboards_view"),
        ("Home",         "show_home_view"),
        ("Events",       "show_events_view"),
        ("Trades",       "show_trades_view"),
    ]

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.button_bar = QHBoxLayout()
        self.button_bar.setContentsMargins(0, 0, 0, 0)
        self.button_bar.setSpacing(0)
        self.root_layout.addLayout(self.button_bar)

        self._show_buttons()

    def refresh(self):
        self._clear()
        if Session.blocking_state:
            self._show_warning()
        else:
            if Session.prompt_message:
                self._show_prompt()
            self._show_buttons()

    def _clear(self):
        while self.button_bar.count():
            item = self.button_bar.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for i in reversed(range(self.root_layout.count())):
            item = self.root_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.setFixedHeight(48)

    def _show_buttons(self):
        for text, method in self._BUTTONS:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet(FOOTER_BUTTON_STYLE)
            btn.clicked.connect(getattr(self.app, method))
            self.button_bar.addWidget(btn, stretch=1)

    def _show_prompt(self):
        prompt_label = QLabel(Session.prompt_message)
        prompt_label.setWordWrap(True)
        prompt_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt_label.setFixedHeight(24)
        prompt_label.setStyleSheet("""
            background-color: #2E7D32;
            color: #FFFFFF;
            font-size: 12px;
            font-weight: bold;
            padding: 0 8px;
        """)
        self.root_layout.insertWidget(0, prompt_label)
        self.setFixedHeight(72)

    def _show_warning(self):
        self.setFixedHeight(100)
        self.app.show_home_view()
        warning_label = QLabel(Session.warning_message or "Server connection has been lost. Please reload the app.")
        warning_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_label.setStyleSheet(FOOTER_WARNING_STYLE)
        self.root_layout.addWidget(warning_label)

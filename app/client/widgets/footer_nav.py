from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from app.client.session import Session


class FooterNav(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self._build_ui()

    def _build_ui(self):
        # Only create root layout once
        if not hasattr(self, "root_layout"):
            self.root_layout = QVBoxLayout(self)
            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.root_layout.setSpacing(0)

        # Button bar
        if not hasattr(self, "button_bar"):
            self.button_bar = QHBoxLayout()
            self.button_bar.setContentsMargins(0, 0, 0, 0)
            self.button_bar.setSpacing(0)
            self.root_layout.addLayout(self.button_bar)

        # Build/update buttons
        buttons = [
            ("League", self.app.show_league_view),
            ("Team", self.app.show_team_view),
            ("Players", self.app.show_players_view),
            ("Leaderboards", self.app.show_leaderboards_view),
        ]
        if not Session.blocking_state:
            for text, callback in buttons:
                btn = QPushButton(text)
                btn.clicked.connect(callback)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedHeight(48)
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 14px;
                        font-weight: bold;
                        background-color: #4200ff;
                        color: white;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #642bff;
                    }
                    QPushButton:pressed {
                        background-color: #3900d5;
                    }
                """)
                self.button_bar.addWidget(btn, stretch=1)

        # Warning label
        if Session.warning_message:
            if not hasattr(self, "warning_label"):
                self.setFixedHeight(100)
                warning_label = QLabel(Session.warning_message)
                warning_label.setStyleSheet("""
                    QLabel {
                        background-color: #700000;
                        color: #ffffff;
                        font-size: 16px;
                        font-weight: bold;
                        padding-left: 10px;
                        padding-right: 10px;
                    }
                """)
                warning_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                warning_label.setWordWrap(True)
                warning_label.setText(Session.warning_message)
                self.root_layout.addWidget(warning_label)
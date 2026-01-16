from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt


class FooterNav(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QWidget {
                background-color: #1f1f1f;
                border-top: 1px solid #333333;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        buttons = [
            ("League", self.app.show_league_view),
            ("Team", self.app.show_team_view),
            ("Players", self.app.show_players_view),
            ("Leaderboards", self.app.show_leaderboards_view),
        ]

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
                }
                QPushButton:hover {
                    background-color: #642bff;
                }
                QPushButton:pressed {
                    background-color: #3900d5;
                }
            """)
            layout.addWidget(btn, stretch=1)
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
import webbrowser


class HeaderBar(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-bottom: 1px solid #dddddd;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        layout.addStretch()

        help_button = QPushButton("Help")
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.clicked.connect(self._open_help)

        logout_button = QPushButton("Log out")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.clicked.connect(self._logout)

        for btn in (help_button, logout_button):
            btn.setFixedHeight(24)
            btn.setFixedWidth(48)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 12px;
                    color: #333333;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)

        layout.addWidget(help_button)
        layout.addWidget(logout_button)

    def _open_help(self):
        webbrowser.open(
            "https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs"
        )

    def _logout(self):
        from app.client.session import Session
        from app.services.session_store import SessionStore

        Session.reset()
        SessionStore.clear()
        self.app.show_login_view()
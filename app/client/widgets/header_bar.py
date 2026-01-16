from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt

import webbrowser

from app.client.session import Session


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
        layout.setSpacing(10)

        # ----- Banner -----

        if Session.banner_message != None:
            self.banner_label = QLabel(Session.banner_message)
            self.banner_label.setAlignment(
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            )

            self.banner_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred
            )

            self.banner_label.setStyleSheet("""
                QLabel {
                    background-color: #9ccfff;
                    color: #1661a8;
                    font-size: 12px;
                    padding-left: 10px;
                    padding-right: 10px;
                }
            """)

            layout.addWidget(self.banner_label)
        else:
            layout.addStretch()

        # ----- Buttons -----
        help_button = QPushButton("Help")
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.clicked.connect(self._open_help)

        logout_button = QPushButton("Log out")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.clicked.connect(self._logout)

        for btn in (help_button, logout_button):
            btn.setFixedHeight(32)
            btn.setFixedWidth(64)
        
        help_button.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 12px;
                color: #000000;
                background-color: #ffffff;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)

        logout_button.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 12px;
                color: #ffffff;
                background-color: #a80000;
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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav
from app.client.session import Session


class HomeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # header
        root_layout.addWidget(HeaderBar(self.app))

        # main
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        content_layout.setContentsMargins(200,0,200,0)

        # ----- welcome block -----
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setSpacing(15)

        welcome_title = QLabel(f"Welcome back, {Session.user}")
        welcome_title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #222;
            }
        """)

        welcome_subtitle = QLabel(
"Welcome to the first Street Fighter 6 Fantasy League! If you're reading this, you've been selected to beta test this application.\n\n" \

"Everything should be functioning without error, keyword there being everything. What's required from you is to break this software in any way possible. Whether you find a way to join a league while you're already in one, or find a way to make those footer buttons look funky, everything is fair game.\n\n" \

"Keep notes of everything you break, and how you broke it too. There'll be somewhere in the discord you can write your notes down, and I'll start working on them one by one. There will likely also be wider scale tests where I trial some admin functions (such as blocking the software server-side) and when it's time for those I'll let you know.\n\n" \

"Other than that, enjoy! Although remember, I can see everything, so keep those league names clean..."
        )
        welcome_subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #555;
            }
        """)
        welcome_subtitle.setWordWrap(True)

        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)

        content_layout.addWidget(welcome_container)

        root_layout.addWidget(content, stretch=1)

        # footer
        root_layout.addWidget(FooterNav(self.app))

        self.setLayout(root_layout)
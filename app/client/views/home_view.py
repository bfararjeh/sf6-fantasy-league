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
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(content, stretch=1)

        # footer
        root_layout.addWidget(FooterNav(self.app))

        self.setLayout(root_layout)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout
)

from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.spinner import SpinnerWidget

class LoadingView(QWidget):
    def __init__(self, app):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        spinner = SpinnerWidget(size=48, color="#4200FF")

        layout.addStretch()
        layout.addWidget(spinner, alignment= Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
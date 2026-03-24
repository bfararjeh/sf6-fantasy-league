from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from app.client.widgets.spinner import SpinnerWidget


class LoadingView(QWidget):
    def __init__(self, app):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(SpinnerWidget(size=48, color="#4200FF"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

from pathlib import Path
import sys
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QSize
from PyQt6.QtWidgets import QPushButton, QApplication
from PyQt6.QtGui import QIcon
from app.client.controllers.resource_path import ResourcePath
from app.client.theme import *

class RefreshButton(QPushButton):
    refresh_requested = pyqtSignal()

    def __init__(self, cooldown: int = 5, parent=None):
        super().__init__(parent)

        self.cooldown = cooldown  # seconds
        self._last_clicked = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(BUTTON_STYLESHEET_B)
        icon_path = ResourcePath.ICONS / "refresh.svg"
        icon = QIcon(str(icon_path))
        icon.addFile(str(icon_path), mode=QIcon.Mode.Disabled)
        self.setIcon(icon)
        self.setIconSize(QSize(32, 32))
        self.clicked.connect(self._on_click)

    def _on_click(self):
        self.setDisabled(True)
        QApplication.processEvents()
        self.refresh_requested.emit()

        QTimer.singleShot(self.cooldown * 1000, self._enable_button)

    def _enable_button(self):
        self.setDisabled(False)

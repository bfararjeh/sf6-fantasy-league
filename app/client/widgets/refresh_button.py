from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QPushButton, QApplication

class RefreshButton(QPushButton):
    refresh_requested = pyqtSignal()

    def __init__(self, cooldown: int = 5, parent=None):
        super().__init__(parent)
        self.cooldown = cooldown  # seconds
        self._last_clicked = None

        self.setFixedSize(64, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("Refresh")
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.clicked.connect(self._on_click)

    def _on_click(self):
        self.setDisabled(True)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #cccccc;
            }
        """)
        self.setText("Refreshing")
        QApplication.processEvents()
        self.refresh_requested.emit()
        self.setText("Refreshed!")

        QTimer.singleShot(self.cooldown * 1000, self._enable_button)

    def _enable_button(self):
        self.setDisabled(False)
        self.setText("Refresh")
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #ffffff;
            }
        """)
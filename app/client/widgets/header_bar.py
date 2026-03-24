from datetime import datetime, timezone, timedelta
import random

from PyQt6.QtWidgets import (
    QApplication,
    QWidget, 
    QHBoxLayout, 
    QPushButton, 
    QLabel,
    QSizePolicy
)

from PyQt6.QtCore import QTimer, Qt, QSize, pyqtSignal

from PyQt6.QtGui import QIcon

from app.client.controllers.session import Session
from app.client.controllers.resource_path import ResourcePath

from app.client.controllers.sound_manager import SoundManager
from app.client.theme import *
from app.client.widgets.settings_dialog import SettingsDialog

class RefreshButton(QPushButton):
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

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
        SoundManager.play("button")

        QTimer.singleShot(5000, self._enable_button)

    def _enable_button(self):
        self.setDisabled(False)


class HeaderBar(QWidget):
    '''
    Header bar visible on every view.
    '''
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.setMinimumHeight(40)

        # create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.setSpacing(10)

        # banner created when there's a message to display
        if Session.banner_message != None:
            msg = Session.banner_message
        else:
            msg = "Welcome to Fantasy Street Fighter 6!"

        self.banner_label = QLabel(msg)
        self.banner_label.setWordWrap(True)
        self.banner_label.setStyleSheet(BANNER_LABEL_STYLESHEET)
        self.banner_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.banner_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.banner_label, stretch=1)

        # buttons
        help_button = QPushButton()
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "help.svg"
        help_button.setIcon(QIcon(str(icon)))
        help_button.setIconSize(QSize(32, 32))
        help_button.clicked.connect(self.app.open_help)

        logout_button = QPushButton()
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.setStyleSheet(BUTTON_STYLESHEET_C)
        icon = ResourcePath.ICONS / "logout.svg"
        logout_button.setIcon(QIcon(str(icon)))
        logout_button.setIconSize(QSize(32, 32))
        logout_button.clicked.connect(self.app.logout)

        settings_button = QPushButton()
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "settings.svg"
        settings_button.setIcon(QIcon(str(icon)))
        settings_button.setIconSize(QSize(32, 32))
        settings_button.clicked.connect(lambda: SettingsDialog(self).exec())

        self.refresh_button = RefreshButton()

        layout.addWidget(self.refresh_button)
        layout.addWidget(help_button)
        layout.addWidget(settings_button)
        layout.addWidget(logout_button)

    def refresh(self):
        layout = self.layout()

        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

        self.banner_label = QLabel()
        self.banner_label.setWordWrap(True)
        self.banner_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.banner_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # banner created depending on message
        if Session.banner_message != None and (datetime.now(timezone.utc) - datetime.fromisoformat(Session.updated_at)) < timedelta(days=7):
            self.banner_label.setStyleSheet(BANNER_LABEL_STYLESHEET_IMPORTANT)
            msg = Session.banner_message
        else:
            self.banner_label.setStyleSheet(BANNER_LABEL_STYLESHEET)
            with open(str(ResourcePath.TEXTS / "banner_flavour.txt"), "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            msg = random.choice(lines) if lines else "Welcome to Fantasy Street Fighter 6!"

        self.banner_label.setText(msg)
        layout.insertWidget(0, self.banner_label, stretch=1)

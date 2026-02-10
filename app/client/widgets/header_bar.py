from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QPushButton, 
    QLabel,
    QSizePolicy
)

from PyQt6.QtCore import Qt, QSize

from PyQt6.QtGui import QIcon

from app.client.controllers.session import Session
from app.client.controllers.resource_path import ResourcePath
from app.client.widgets.refresh_button import RefreshButton

from app.client.theme import *

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
            self.banner_label = QLabel(Session.banner_message)
            self.banner_label.setWordWrap(True)
            self.banner_label.setStyleSheet(BANNER_LABEL_STYLESHEET)
            self.banner_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.banner_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            layout.addWidget(self.banner_label, stretch=1)

        else:
            layout.addStretch()

        # help and logout button
        help_button = QPushButton()
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.clicked.connect(self.app.open_help)
        help_button.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "help.svg"
        help_button.setIcon(QIcon(str(icon)))
        help_button.setIconSize(QSize(32, 32))

        logout_button = QPushButton()
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.clicked.connect(self.app.logout)
        logout_button.setStyleSheet(BUTTON_STYLESHEET_C)
        icon = ResourcePath.ICONS / "logout.svg"
        logout_button.setIcon(QIcon(str(icon)))
        logout_button.setIconSize(QSize(32, 32))

        self.refresh_button = RefreshButton()

        layout.addWidget(self.refresh_button)
        layout.addWidget(help_button)
        layout.addWidget(logout_button)
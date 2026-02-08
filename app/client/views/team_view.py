from pathlib import Path

from datetime import datetime
import sys

from PyQt6.QtWidgets import (
    QWidget, 
    QLabel, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout, 
    QComboBox,
    QLineEdit,
    QGroupBox,
    QFrame,
    QSizePolicy,
    QScrollArea,
)

from PyQt6.QtCore import Qt, QTimer

from PyQt6.QtGui import QPixmap

from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

class TeamView(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app



        # build static ui then update
        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.header.refresh_button.refresh_requested.connect(lambda: self._refresh(force=1))
        
        self.footer = FooterNav(self.app)

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(10)

        self.scroll.setWidget(self.content_widget)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(25)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
            }
        """)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(self.scroll, stretch=1)
        self.root_layout.addWidget(self.status_label)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        self.team_creator = self._build_team_creator()
        self.team_info = self._build_team_info()
        self.draft_picker = self._build_draft_picker()
        self.team_overview = self._build_roster_overview()
        self.player_stats = self._build_player_stat_section()

        self.content_layout.addWidget(self.team_creator)
        self.content_layout.addWidget(self.team_info)
        self.content_layout.addWidget(self.draft_picker)
        self.content_layout.addWidget(self.team_overview)
        self.content_layout.addWidget(self.player_stats)



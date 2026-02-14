from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar

class EventView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.even_data = Session.event_data
        self.dist_data = Session.dist_data
        
        # build static ui then update
        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.header.refresh_button.refresh_requested.connect(lambda: self._refresh(force=1))
        
        self.footer = FooterNav(self.app)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(SCROLL_STYLESHEET)

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(10)

        scroll.setWidget(self.content_widget)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(scroll, stretch=1)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        self.content_layout.addWidget(self._build_info())


# -- BUILDERS --

    def _build_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        events = QLabel("Events")
        events.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold;
        """)

        layout.addWidget(events)

        return container
    

# -- LAYOUT STUFF --
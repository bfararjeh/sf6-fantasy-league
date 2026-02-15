from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QIcon
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

        self.event_data = Session.event_data
        self.dist_data = Session.dist_data

        self.current_event_idx = 0
        self.event_widgets = []
        
        # build static ui then update
        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.footer = FooterNav(self.app)

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(10)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(self.content_widget, stretch=1)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        info_widget = self._build_info()

        self.content_layout.addWidget(info_widget)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self._build_carousel())
        self.content_layout.addStretch()
        self.content_layout.addSpacerItem(QSpacerItem(0, info_widget.sizeHint().height()))



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

    def _build_carousel(self):
        """3-image carousel: center clickable, sides as previews."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(50)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        help_button = QPushButton()
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.clicked.connect(self.app.open_help)
        help_button.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "help.svg"
        help_button.setIcon(QIcon(str(icon)))
        help_button.setIconSize(QSize(32, 32))

        # Left arrow
        self.left_arrow = QPushButton()
        self.left_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_arrow.clicked.connect(lambda: self._change_event(-1))
        self.left_arrow.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "arrow_left.svg"
        self.left_arrow.setIcon(QIcon(str(icon)))
        self.left_arrow.setIconSize(QSize(32, 32))

        layout.addWidget(self.left_arrow)
        layout.addStretch()

        # Three event placeholders: left, center, right
        self.left_preview = QLabel()
        self.left_preview.setFixedSize(200, 200)
        self.left_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.center_display = QLabel()
        self.center_display.setFixedSize(300, 300)
        self.center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_display.mousePressEvent = lambda e: self._on_event_clicked(self.event_data[self.current_event_idx])

        self.right_preview = QLabel()
        self.right_preview.setFixedSize(200, 200)
        self.right_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.left_preview)
        layout.addWidget(self.center_display)
        layout.addWidget(self.right_preview)

        # Right arrow
        self.right_arrow = QPushButton()
        self.right_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_arrow.clicked.connect(lambda: self._change_event(1))
        self.right_arrow.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "arrow_right.svg"
        self.right_arrow.setIcon(QIcon(str(icon)))
        self.right_arrow.setIconSize(QSize(32, 32))


        layout.addStretch()
        layout.addWidget(self.right_arrow)

        # Build event images
        self.event_widgets = []
        for event in self.event_data:
            widget = self._build_event_image(event, size=300)
            self.event_widgets.append(widget)

        # Initialize carousel
        if self.event_widgets:
            self._update_event_display()

        return container

    def _build_event_image(self, event, size=300):
        image = QLabel()
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap()

        try:
            pixmap.loadFromData(event["image_bytes"])
            if pixmap.isNull():
                pixmap = QPixmap(str(ResourcePath.EVENTS / "placeholder.png"))

        except Exception:
            pixmap = QPixmap(str(ResourcePath.EVENTS / "placeholder.png"))

        image.setPixmap(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        
        return image


# -- BUTTON METHODS --


# -- LAYOUT STUFF --

    def _change_event(self, delta: int):
        if not self.event_widgets:
            return
        self.current_event_idx = (self.current_event_idx + delta) % len(self.event_widgets)
        self._update_event_display()

    def _update_event_display(self):
        """Update center and side previews for carousel."""
        total = len(self.event_widgets)
        if total == 0:
            return

        center_idx = self.current_event_idx
        left_idx = (center_idx - 1) % total
        right_idx = (center_idx + 1) % total

        # Center is large and clickable
        self.center_display.setPixmap(self.event_widgets[center_idx].pixmap())
        
        # Left and right previews are smaller, not clickable
        left_pix = self.event_widgets[left_idx].pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        right_pix = self.event_widgets[right_idx].pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )

        self.left_preview.setPixmap(left_pix)
        self.right_preview.setPixmap(right_pix)

    def _on_event_clicked(self, event):
        print(f"Clicked event: {event['name']}")
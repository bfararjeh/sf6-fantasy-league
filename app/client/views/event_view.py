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

from datetime import datetime, timezone

class EventView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.event_data = Session.event_data
        self.dist_data = Session.dist_data

        now = datetime.now(timezone.utc)

        self.current_event_idx = next(
            (
                i for i, item in enumerate(self.event_data)
                if datetime.fromisoformat(item["start_weekend"]) > now
            ),
            len(self.event_data)-1
        )

        self.events = []
        
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
        self.timeline_widget = self._build_timeline()

        self.content_layout.addWidget(info_widget)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self._build_carousell())
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.timeline_widget)



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

    def _build_carousell(self):
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
        self.left_arrow.setIconSize(QSize(32, 128))

        layout.addWidget(self.left_arrow)
        layout.addStretch()

        # Three event placeholders: left, center, right
        self.left_preview = QLabel()
        self.left_preview.setFixedWidth(200)
        self.left_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)

        self.center_display = QLabel()
        self.center_display.setFixedWidth(300)
        self.center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_display.mousePressEvent = lambda e: self._on_event_clicked(self.event_data[self.current_event_idx])

        self.event_name_label = QLabel("Title")
        self.event_date_label = QLabel("Date")
        self.event_tier_label = QLabel("Tier")

        center_layout.addWidget(self.event_name_label)
        center_layout.addWidget(self.event_tier_label)
        center_layout.addWidget(self.center_display)
        center_layout.addWidget(self.event_date_label)

        self.right_preview = QLabel()
        self.right_preview.setFixedWidth(200)
        self.right_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.left_preview)
        layout.addWidget(center_container)
        layout.addWidget(self.right_preview)

        # Right arrow
        self.right_arrow = QPushButton()
        self.right_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_arrow.clicked.connect(lambda: self._change_event(1))
        self.right_arrow.setStyleSheet(BUTTON_STYLESHEET_B)
        icon = ResourcePath.ICONS / "arrow_right.svg"
        self.right_arrow.setIcon(QIcon(str(icon)))
        self.right_arrow.setIconSize(QSize(32, 128))


        layout.addStretch()
        layout.addWidget(self.right_arrow)

        # Build event images
        self.events = []
        for event in self.event_data:
            widget = self._build_event_iamge(event, size=300)
            self.events.append({
                "image": widget,
                "name": event.get("name", "N/A"),
                "tier": event.get("tier", "N/A"),
                "date": datetime.fromisoformat(event.get("start_weekend", "N/A")).date()
            })

        # Initialize carousel
        if self.events:
            self._update_event_display()

        return container

    def _build_event_iamge(self, event, size=300):
        image = QLabel()
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

    def _build_timeline(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Horizontal line of dots + lines
        dots_widget = QWidget()
        dots_layout = QHBoxLayout(dots_widget)
        dots_layout.setSpacing(18)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timeline_dots = []
        self.timeline_labels = []

        month_names = ["M", "A", "M", "J", "J", "A", "S",
                    "O", "N", "D", "J", "F", "M"]

        for i, month in enumerate(month_names):
            dot_container = QWidget()
            dot_layout = QVBoxLayout(dot_container)
            dot_layout.setContentsMargins(0, 0, 0, 0)
            dot_layout.setSpacing(4)
            dot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            dot = QLabel()
            dot.setFixedSize(14, 14)
            dot.setStyleSheet("background-color: #444; border-radius: 7px;")
            self.timeline_dots.append(dot)

            label = QLabel(month)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 10px; color: #888;")
            self.timeline_labels.append(label)

            dot_layout.addWidget(dot)
            dot_layout.addWidget(label)
            dot_container.setLayout(dot_layout)
            dots_layout.addWidget(dot_container)

            # Add connecting line except after last dot
            if i < len(month_names) - 1:
                line = QWidget()
                line.setFixedSize(20, 2)
                line.setStyleSheet("background-color: #333;")
                dots_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(dots_widget)
        return container




# -- BUTTON METHODS --


# -- LAYOUT STUFF --

    def _change_event(self, delta: int):
        if not self.events:
            return
        self.current_event_idx = (self.current_event_idx + delta) % len(self.events)
        self._update_event_display()

    def _update_event_display(self):
        """Update center and side previews for carousel."""
        total = len(self.events)
        if total == 0:
            return

        center_idx = self.current_event_idx
        left_idx = (center_idx - 1) % total
        right_idx = (center_idx + 1) % total

        # Center is large and clickable
        self.center_display.setPixmap(self.events[center_idx].get("image").pixmap())
        
        # Left and right previews are smaller, not clickable
        left_pix = self.events[left_idx].get("image").pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        right_pix = self.events[right_idx].get("image").pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )

        self.left_preview.setPixmap(left_pix)
        self.right_preview.setPixmap(right_pix)

        self.event_name_label.setText(str(self.events[center_idx].get("name", "N/A")))
        self.event_date_label.setText(str(self.events[center_idx].get("date", "N/A")))
        self.event_tier_label.setText(str(self.events[center_idx].get("tier", "N/A")))

        date = str(self.events[center_idx].get("date", "N/A"))
        self._update_timeline(date)

    def _on_event_clicked(self, event):
        print(f"Clicked event: {event['name']}")

    def _update_timeline(self, event_date_str):
        dt_event = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        
        # Selected event month/year
        sel_year, sel_month = dt_event.year, dt_event.month
        
        now = datetime.now()
        now_year, now_month = now.year, 7
        
        for i, dot in enumerate(self.timeline_dots):
            # Map index → month/year
            if i <= 9:  # MAR-DEC 2026
                dot_year = 2026
                dot_month = i + 3
            else:       # JAN-MAR 2027
                dot_year = 2027
                dot_month = i - 9
            
            # Selected event
            if dot_year == sel_year and dot_month == sel_month:
                color = "#00D4FF"
            # Current month
            elif dot_year == now_year and dot_month == now_month:
                color = "#FFBCCA"
            # Past months (before today)
            elif (dot_year < now_year) or (dot_year == now_year and dot_month < now_month):
                color = "#111111"
            # Future months
            else:
                color = "#444444"

            dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")

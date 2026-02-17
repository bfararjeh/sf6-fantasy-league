from PyQt6.QtCore import Qt, QSize, QTimer
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
    QStackedWidget,
)
from PyQt6.QtGui import QFontMetrics, QPixmap

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
        self.event_detail_cache = {}
        self.current_detail_event_id = None

        now = datetime.now(timezone.utc)

        self.current_event_idx = next((
            i for i, item in enumerate(self.event_data)
            if datetime.fromisoformat(item["start_weekend"]) > now
            ),
            len(self.event_data)-1
        )

        self.next_up_index = self.current_event_idx
        self.events = []
        
        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.footer = FooterNav(self.app)

        self.view_stack = QStackedWidget()

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(0)

        self.main_page = QWidget()
        self.main_layout = QVBoxLayout(self.main_page)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.addWidget(self.content_widget)

        self.view_stack.addWidget(self.main_page)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(self.view_stack, stretch=1)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        info_widget = self._build_info()
        self.timeline_widget = self._build_timeline()
        self.next_up_label = self._build_next_up()

        self.content_layout.addWidget(info_widget)
        self.content_layout.addWidget(self._build_carousell())
        self.content_layout.addWidget(self.next_up_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.timeline_widget)


# -- BUILDERS: MAIN --

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
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(50)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # arrows
        icon = ResourcePath.ICONS / "arrow_left.svg"
        self.left_arrow = QPushButton()
        self.left_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_arrow.setStyleSheet(BUTTON_STYLESHEET_B)
        self.left_arrow.setIcon(QIcon(str(icon)))
        self.left_arrow.setIconSize(QSize(32, 128))
        self.left_arrow.clicked.connect(lambda: self._change_event(-1))

        icon = ResourcePath.ICONS / "arrow_right.svg"
        self.right_arrow = QPushButton()
        self.right_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_arrow.setStyleSheet(BUTTON_STYLESHEET_B)
        self.right_arrow.setIcon(QIcon(str(icon)))
        self.right_arrow.setIconSize(QSize(32, 128))
        self.right_arrow.clicked.connect(lambda: self._change_event(1))

        # placeholders for left, center, and right
        self.left_preview = QLabel()
        self.left_preview.setFixedWidth(200)
        self.left_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setSpacing(0)

        self.center_display = QLabel()
        self.center_display.setFixedWidth(300)
        self.center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_display.mousePressEvent = lambda e: self._on_event_clicked(self.event_data[self.current_event_idx])

        self.event_name_label = QLabel("")
        self.event_name_label.setFixedHeight(60)
        self.event_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_name_label.setStyleSheet("""
            font-weight: bold;
        """)

        self.event_date_label = QLabel("")
        self.event_date_label.setFixedHeight(40)
        self.event_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_date_label.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
        """)

        self.event_tier_label = QLabel("")
        self.event_tier_label.setFixedHeight(40)
        self.event_tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_tier_label.setStyleSheet("""
            font-size: 20px;
        """)

        center_layout.addWidget(self.event_name_label)
        center_layout.addWidget(self.center_display)
        center_layout.addWidget(self.event_date_label)
        center_layout.addWidget(self.event_tier_label)

        self.right_preview = QLabel()
        self.right_preview.setFixedWidth(200)
        self.right_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.left_arrow)
        layout.addStretch()
        layout.addWidget(self.left_preview)
        layout.addWidget(center_container)
        layout.addWidget(self.right_preview)
        layout.addStretch()
        layout.addWidget(self.right_arrow)

        # build event widgets and store data with them
        self.events = []
        for event in self.event_data:
            widget = self._build_event_image(event, size=250)
            self.events.append({
                "image": widget,
                "name": event.get("name", "N/A"),
                "tier": event.get("tier", 0),
                "complete": event.get("complete", False),
                "date": datetime.fromisoformat(event.get("start_weekend", "N/A")).date()
            })

        # init carousel
        if self.events:
            self._update_event_display()

        return container

    def _build_event_image(self, event, size=300):
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

        # row of dots + lines
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
            label.setStyleSheet("font-size: 14px; color: #AAAAAA; font-weight: bold;")
            self.timeline_labels.append(label)

            dot_layout.addWidget(dot)
            dot_layout.addWidget(label)
            dot_container.setLayout(dot_layout)
            dots_layout.addWidget(dot_container)

            # connecting lines bar last
            if i < len(month_names) - 1:
                line = QWidget()
                line.setFixedSize(20, 2)
                line.setStyleSheet("background-color: #333;")
                dots_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(dots_widget)
        return container

    def _build_next_up(self):
        label = QLabel()
        label.setFixedWidth(200)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return label


# -- BUILDERS: DETAILED --  

    def _build_event_detail_view(self, event):
        root = QWidget()
        root_layout = QHBoxLayout(root)

        # -- LEFT SIDE --
        left = QWidget()
        left_layout = QVBoxLayout(left)

        back_btn = QPushButton("Back")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(BUTTON_STYLESHEET_D)
        back_btn.clicked.connect(self._return_to_main)

        image = self._build_event_image(event, size=300)
        name = QLabel(event.get("name","N/A"))
        date = QLabel(str(datetime.fromisoformat(event.get("start_weekend")).date()))
        tier = QLabel(f"Tier {event.get('tier','N/A')}")

        left_layout.addWidget(image)
        left_layout.addWidget(name)
        left_layout.addWidget(date)
        left_layout.addWidget(tier)
        left_layout.addStretch()
        left_layout.addWidget(back_btn)

        # -- RIGHT SIDE --
        right = QWidget()
        right_layout = QVBoxLayout(right)

        btn_row = QHBoxLayout()

        self.active_filter = "all"

        all_btn = QPushButton("All")
        me_btn = QPushButton("Me")
        league_btn = QPushButton("League")

        for btn in [all_btn, me_btn, league_btn]:
            btn.setStyleSheet(BUTTON_STYLESHEET_A)

        btn_row.addWidget(all_btn)
        btn_row.addWidget(me_btn)
        btn_row.addWidget(league_btn)

        # ---- Score Container ----
        score_container = QStackedWidget()

        loading_label = QLabel("Loading...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_label = QLabel("No data loaded")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        score_container.addWidget(empty_label)
        score_container.addWidget(loading_label)

        right_layout.addLayout(btn_row)
        right_layout.addWidget(score_container, stretch=1)

        root_layout.addWidget(left)
        root_layout.addWidget(right, stretch=1)

        # -- STATE STORAGE --
        root.score_state = {
            "loaded": {
                "all": False,
                "me": False,
                "league": False
            },
            "widgets": {},
            "score_container": score_container,
            "loading_widget": loading_label,
            "empty_widget": empty_label,
            "buttons": {
                "all": all_btn,
                "me": me_btn,
                "league": league_btn
            },
            "event": event
        }

        # -- BUTTON HOOKS --

        all_btn.clicked.connect(lambda: self._on_filter_clicked(root, "all"))
        me_btn.clicked.connect(lambda: self._on_filter_clicked(root, "me"))
        league_btn.clicked.connect(lambda: self._on_filter_clicked(root, "league"))

        self._set_active_score_button(root, "all")

        return root


# -- BUTTON METHODS --

    def _on_event_clicked(self, event):
        event_id = event.get("id")

        if event_id not in self.event_detail_cache:
            widget = self._build_event_detail_view(event)
            self.event_detail_cache[event_id] = widget
            self.view_stack.addWidget(widget)

        self.current_detail_event_id = event_id
        self.view_stack.setCurrentWidget(self.event_detail_cache[event_id])

    def _on_filter_clicked(self, root, filter_type):
        if filter_type == self.active_filter:
            print("nu uh")
            return

        self.active_filter = filter_type
        self._select_score_tab(root, filter_type)

    def _return_to_main(self):
        self.view_stack.setCurrentWidget(self.main_page)

    def _set_active_score_button(self, root, tab):
        btns = root.score_state["buttons"]

        active = BUTTON_STYLESHEET_A_ACTIVE
        inactive = BUTTON_STYLESHEET_A

        for name, btn in btns.items():
            btn.setStyleSheet(active if name == tab else inactive)

    def _select_score_tab(self, root, tab):
        state = root.score_state
        self._set_active_score_button(root, tab)

        container = state["score_container"]

        # If already loaded → show
        if state["loaded"][tab]:
            container.setCurrentWidget(state["widgets"][tab])
            return

        # Otherwise show loading
        container.setCurrentWidget(state["loading_widget"])

        # Simulate async load trigger point
        self._load_score_data(root, tab)

    def _load_score_data(self, root, tab):
        state = root.score_state
        event = state["event"]

        # TODO Replace with real API call
        QTimer.singleShot(2000, lambda: self._finish_score_load(root, tab))

    def _finish_score_load(self, root, tab):
        state = root.score_state

        # Placeholder result widget
        result = QLabel(f"{tab.upper()} SCORE DATA READY")
        result.setAlignment(Qt.AlignmentFlag.AlignCenter)

        state["score_container"].addWidget(result)
        state["widgets"][tab] = result
        state["loaded"][tab] = True

        state["score_container"].setCurrentWidget(result)

# -- LAYOUT STUFF --

    def _change_event(self, delta: int):
        if not self.events:
            return
        
        self.current_event_idx = (self.current_event_idx + delta) % len(self.events)
        self._update_event_display()

    def _update_event_display(self):
        total = len(self.events)
        if total == 0:
            return

        # update indexes
        center_idx = self.current_event_idx
        left_idx = (center_idx - 1) % total
        right_idx = (center_idx + 1) % total

        # update center and side iamges
        center_pix = self.events[center_idx].get("image").pixmap()
        left_pix = self.events[left_idx].get("image").pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        right_pix = self.events[right_idx].get("image").pixmap().scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.center_display.setPixmap(center_pix)
        self.left_preview.setPixmap(left_pix)
        self.right_preview.setPixmap(right_pix)

        # update labels + timeline
        self._fit_text_to_width(self.event_name_label, str(self.events[center_idx].get("name", "N/A")), 300)
        self.event_date_label.setText(str(self.events[center_idx].get("date", "N/A")))

        if self.events[center_idx].get("tier", 0) > 0:
            self.event_tier_label.setText("Tier " + str(self.events[center_idx].get("tier", "N/A")))
        else:
            self.event_tier_label.setText("Non-standard Tier")

        date = str(self.events[center_idx].get("date", "N/A"))
        self._update_next_up(center_idx=center_idx)
        self._update_timeline(date)

    def _update_timeline(self, event_date_str):
        dt_event = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        
        # selected month/year
        sel_year, sel_month = dt_event.year, dt_event.month
        
        now = datetime.now()
        now_year, now_month = now.year, now.month
        
        for i, dot in enumerate(self.timeline_dots):
            if i <= 9:  # MAR-DEC 2026
                dot_year = 2026
                dot_month = i + 3
            else:       # JAN-MAR 2027
                dot_year = 2027
                dot_month = i - 9
            
            # selected
            if dot_year == sel_year and dot_month == sel_month:
                color = "#008CFF"
            # current
            elif dot_year == now_year and dot_month == now_month:
                color = "#DA68C1"
            # past
            elif (dot_year < now_year) or (dot_year == now_year and dot_month < now_month):
                color = "#272727"
            # future months
            else:
                color = "#646464"

            dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")

    def _update_next_up(self, center_idx):
        library = {
            "future":["#339FF8", "Future Event"],
            "current": ["#3EA702", "Next Up!"],
            "past": ["#DB5A0F", "Past Event"]
            }
        
        # find chosen event index relative to next_up index
        if center_idx < self.next_up_index:
            attributes = library["past"]
        elif center_idx == self.next_up_index:
            attributes = library["current"]
        else:
            attributes = library["future"]

        self.next_up_label.setText(attributes[1])
        self.next_up_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: white;

            background-color: {attributes[0]};

            padding: 6px 10px;
            border-radius: 8px;
        """)

    def _fit_text_to_width(self, label: QLabel, text: str, max_width: int,
                        min_font_size=2, max_font_size=40):
        """
        Adjusts the font size of a label to fit within a specific width 
        restriction.
        """
        if not text or max_width <= 0:
            return

        font = label.font()
        font.setBold(True)
        font_size = min_font_size
        font.setPointSize(font_size)
        metrics = QFontMetrics(font)

        # binary search to find the largest font that fits
        low, high = min_font_size, max_font_size
        best_size = min_font_size

        while low <= high:
            mid = (low + high) // 2
            font.setPointSize(mid)
            metrics = QFontMetrics(font)
            if metrics.boundingRect(text).width() <= max_width:
                best_size = mid  # fits, try bigger
                low = mid + 1
            else:
                high = mid - 1  # too big, try smaller
                
        font.setPointSize(best_size)
        label.setFont(font)
        label.setText(text)

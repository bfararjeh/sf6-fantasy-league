from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QIcon, QFontMetrics
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsColorizeEffect,
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
from PyQt6.QtWidgets import QToolTip
from PyQt6.QtCore import QPoint

from app.client.controllers.async_runner import run_async
from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


# dedicated class and widget for event detail view
@dataclass
class ScoreState:
    event: dict
    score_container: QStackedWidget
    loading_widget: QLabel
    empty_widget: QLabel
    buttons: dict
    loaded: dict = field(default_factory=lambda: {"all": False, "me": False, "league": False})
    active_filter: Optional[str] = None
    widgets: dict = field(default_factory=dict)

class EventDetailWidget(QWidget):
    def __init__(self, state: ScoreState):
        super().__init__()
        self.score_state = state


class EventView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        Session.init_league_data()

        self.event_data = Session.event_data
        self.dist_data = Session.dist_data
        self.event_detail_cache = {}
        self.current_detail_event_id = None

        self.RANK_STYLES = {
            1: "#FFD700",
            2: "#C0C0C0",
            3: "#CD7F32",
            4: "#E4E4E4",
        }

        # now = datetime.now(timezone.utc)
        now = datetime(2026, 12, 12, tzinfo=timezone.utc)
        self.now_year, self.now_month = now.year, now.month

        self.current_event_idx = next(
            (i for i, item in enumerate(self.event_data)
             if datetime.fromisoformat(item["start_weekend"]) > now),
            len(self.event_data) - 1
        )

        self.next_up_index = self.current_event_idx
        self.event_images = []

        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.footer = FooterNav(self.app)

        self.view_stack = QStackedWidget()

        self.main_page = QWidget()
        self.content_layout = QVBoxLayout(self.main_page)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(0)

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
        self.content_layout.addWidget(self._build_carousel())
        self.content_layout.addWidget(self.next_up_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.timeline_widget)


# -- BUILDERS --

    def _build_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        events = QLabel("Events")
        events.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events.setStyleSheet("font-size: 64px; font-weight: bold;")

        layout.addWidget(events)
        return container

    def _build_carousel(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(50)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Arrows
        self.left_arrow = self._make_arrow_button("arrow_left.svg", lambda: self._change_event(-1))
        self.right_arrow = self._make_arrow_button("arrow_right.svg", lambda: self._change_event(1))

        # Side previews
        self.left_preview = QLabel()
        self.left_preview.setFixedWidth(200)
        self.left_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.right_preview = QLabel()
        self.right_preview.setFixedWidth(200)
        self.right_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Centre display
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setSpacing(0)

        self.center_display = QLabel()
        self.center_display.setFixedWidth(300)
        self.center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_display.mousePressEvent = lambda e: self._on_event_clicked(
            self.event_data[self.current_event_idx]
        )

        self.event_name_label = QLabel("")
        self.event_name_label.setFixedHeight(60)
        self.event_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_name_label.setStyleSheet("font-weight: bold;")

        self.event_date_label = QLabel("")
        self.event_date_label.setFixedHeight(40)
        self.event_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_date_label.setStyleSheet("font-weight: bold; font-size: 20px;")

        self.event_tier_label = QLabel("")
        self.event_tier_label.setFixedHeight(40)
        self.event_tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_tier_label.setStyleSheet("font-size: 20px;")

        center_layout.addWidget(self.event_name_label)
        center_layout.addWidget(self.center_display)
        center_layout.addWidget(self.event_date_label)
        center_layout.addWidget(self.event_tier_label)

        layout.addWidget(self.left_arrow)
        layout.addStretch()
        layout.addWidget(self.left_preview)
        layout.addWidget(center_container)
        layout.addWidget(self.right_preview)
        layout.addStretch()
        layout.addWidget(self.right_arrow)

        # Build image widgets once; raw event data stays in self.event_data
        self.event_images = [
            self._build_event_image(event, size=250)
            for event in self.event_data
        ]

        if self.event_images:
            self._update_event_display()

        return container

    def _make_arrow_button(self, icon_filename: str, callback) -> QPushButton:
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BUTTON_STYLESHEET_B)
        btn.setIcon(QIcon(str(ResourcePath.ICONS / icon_filename)))
        btn.setIconSize(QSize(32, 128))
        btn.clicked.connect(callback)
        return btn

    def _build_event_image(self, event, size=300):
        """Load an event image from bytes, falling back to a placeholder."""
        image = QLabel()
        pixmap = self._load_pixmap_from_bytes(
            event.get("image_bytes"),
            str(ResourcePath.EVENTS / "placeholder.png"),
        )
        image.setPixmap(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        return image

    def _load_pixmap_from_bytes(self, data: bytes | None, fallback_path: str) -> QPixmap:
        """Shared helper: load a QPixmap from raw bytes, with a file fallback."""
        pixmap = QPixmap()
        if data:
            try:
                pixmap.loadFromData(data)
            except Exception:
                pass
        if pixmap.isNull():
            pixmap = QPixmap(fallback_path)
        return pixmap

    def _load_pixmap_from_file(self, path: str, fallback_path: str) -> QPixmap:
        """Shared helper: load a QPixmap from a file path, with a fallback."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = QPixmap(fallback_path)
        return pixmap

    def _build_timeline(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dots_widget = QWidget()
        dots_layout = QHBoxLayout(dots_widget)
        dots_layout.setSpacing(18)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timeline_dots = []
        self.timeline_labels = []

        month_names = ["M", "A", "M", "J", "J", "A", "S", "O", "N", "D", "J", "F", "M"]

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


# -- DETAIL BUILDERS --

    def _build_event_detail_view(self, event) -> EventDetailWidget:
        # -- LEFT SIDE --
        left = QWidget()
        left_layout = QVBoxLayout(left)

        back_btn = QPushButton("Back")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        back_btn.clicked.connect(self._return_to_main)

        image = self._build_event_image(event, size=300)

        name = QLabel()
        self._fit_text_to_width(name, str(event.get("name", "N/A")), 300)

        tier_val = event.get("tier", 0)
        tier = QLabel("Tier " + str(tier_val) if tier_val > 0 else "Non-standard Tier")
        date = QLabel(str(datetime.fromisoformat(event.get("start_weekend")).date()))

        for lbl in (name, date, tier):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date.setStyleSheet("font-size: 20px; font-weight: bold;")
        tier.setStyleSheet("font-size: 20px; font-weight: bold;")

        left_layout.addStretch()
        left_layout.addWidget(image)
        left_layout.addWidget(name)
        left_layout.addWidget(date)
        left_layout.addWidget(tier)
        left_layout.addStretch()
        left_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # -- RIGHT SIDE --
        right = QWidget()
        right_layout = QVBoxLayout(right)

        all_btn = QPushButton("All")
        me_btn = QPushButton("Me")
        league_btn = QPushButton("League")
        for btn in (all_btn, me_btn, league_btn):
            btn.setStyleSheet(BUTTON_STYLESHEET_A)

        btn_row = QHBoxLayout()
        btn_row.addWidget(all_btn)
        btn_row.addWidget(me_btn)
        btn_row.addWidget(league_btn)

        score_container = QStackedWidget()
        score_container.setStyleSheet("""
            QStackedWidget {
                border: 2px solid #FFFFFF;
                border-radius: 8px;
            }
        """)

        loading_label = QLabel("Loading...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_label = QLabel("Nothing to see here!")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        score_container.addWidget(empty_label)
        score_container.addWidget(loading_label)

        right_layout.addLayout(btn_row)
        right_layout.addWidget(score_container, stretch=1)

        # -- Assemble root widget with typed state --
        state = ScoreState(
            event=event,
            score_container=score_container,
            loading_widget=loading_label,
            empty_widget=empty_label,
            buttons={"all": all_btn, "me": me_btn, "league": league_btn},
        )
        root = EventDetailWidget(state)
        root_layout = QHBoxLayout(root)
        root_layout.addWidget(left)
        root_layout.addWidget(right, stretch=1)

        all_btn.clicked.connect(lambda: self._on_filter_clicked(root, "all"))
        me_btn.clicked.connect(lambda: self._on_filter_clicked(root, "me"))
        league_btn.clicked.connect(lambda: self._on_filter_clicked(root, "league"))

        return root

    def create_all_score_data(self, data):
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(30)

        if not data:
            empty = QLabel("No data available")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer_layout.addWidget(empty)
            return outer

        # Group entries by rank
        ranks: dict[int, list] = {}
        for entry in data:
            ranks.setdefault(entry["rank"], []).append(entry)

        MAX_PER_ROW = 4

        for rank in sorted(ranks.keys()):
            players = ranks[rank]

            rank_block = QWidget()
            rank_block_layout = QVBoxLayout(rank_block)
            rank_block_layout.setSpacing(20)
            rank_block_layout.setContentsMargins(0, 0, 0, 0)

            rank_label = QLabel(self._format_rank_text(rank, players[0].get("points", 0)))
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            font = rank_label.font()
            font.setBold(True)
            font.setPointSize(self._rank_font_size(rank))
            rank_label.setFont(font)

            if rank in self.RANK_STYLES:
                color = self.RANK_STYLES[rank]
                rank_label.setStyleSheet(f"color: {color};")
                glow = QGraphicsDropShadowEffect()
                glow.setBlurRadius(25)
                glow.setOffset(0)
                glow.setColor(QColor(color))
                rank_label.setGraphicsEffect(glow)

            rank_block_layout.addWidget(rank_label)

            for i in range(0, len(players), MAX_PER_ROW):
                chunk = players[i:i + MAX_PER_ROW]
                image_size = self._size_from_quantity(len(chunk))

                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setSpacing(15)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addStretch()
                for player in chunk:
                    row_layout.addWidget(self._build_player_tile(player, image_size, rank))
                row_layout.addStretch()

                rank_block_layout.addWidget(row_widget)

            outer_layout.addWidget(rank_block)

        outer_layout.addStretch()

        scroll = QScrollArea()
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(outer)
        return scroll

    def create_me_score_data(self, data):
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(30)

        if not data:
            empty = QLabel("No data available")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer_layout.addWidget(empty)
            return outer

        IMAGE_SIZE = 125
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(30)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addStretch()

        for player in data:
            rank = player["rank"]
            points = player["points"]
            inactive = rank is None or points == 0

            tile = self._build_player_tile(player, IMAGE_SIZE, rank, enable_tooltip=False)

            if inactive:
                image_label = tile.layout().itemAt(0).widget()
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor("gray"))
                effect.setStrength(1.0)
                image_label.setGraphicsEffect(effect)

            tile.layout().addWidget(self._make_centered_label(player["player"], bold=True))
            tile.layout().addWidget(self._make_centered_label(self._format_rank_text(rank, points)))
            row_layout.addWidget(tile)

        row_layout.addStretch()

        # Total points summary
        total_points = sum(p["points"] for p in data)
        total_label = self._make_centered_label(f"+{total_points} pts", bold=True)
        total_label.setStyleSheet("font-size: 20px; color: #3EA702;")

        outer_layout.addStretch()
        outer_layout.addWidget(row_widget)
        outer_layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignCenter)
        outer_layout.addStretch()

        return outer

    def create_league_score_data(self, data):
        if not data:
            empty = QLabel("No data available")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return empty

        IMAGE_SIZE = 100

        # Sort members by total points descending
        sorted_members = sorted(
            data.items(),
            key=lambda item: sum(p["points"] for p in item[1].values()),
            reverse=True
        )

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(20)

        for member_rank, (member_name, players) in enumerate(sorted_members, start=1):
            total_points = sum(p["points"] for p in players.values())

            # -- Member block --
            block = QWidget()
            block.setStyleSheet("background-color: #090E2B; border-radius: 8px;")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(15, 15, 15, 15)
            block_layout.setSpacing(10)

            # Header row: rank + member name + total points
            header_layout = QHBoxLayout()
            rank_label = self._make_centered_label(f"#{member_rank}", bold=True)
            rank_label.setStyleSheet("font-size: 20px; color: #AAAAAA;")
            rank_label.setFixedWidth(40)

            name_label = self._make_centered_label(member_name, bold=True)
            name_label.setStyleSheet("font-size: 20px;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            total_label = self._make_centered_label(f"+{total_points} pts", bold=True)
            total_label.setStyleSheet("font-size: 18px; color: #3EA702;")
            total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            header_layout.addWidget(rank_label)
            header_layout.addWidget(name_label)
            header_layout.addStretch()
            header_layout.addWidget(total_label)
            block_layout.addLayout(header_layout)

            # Divider
            divider = QWidget()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #333333;")
            block_layout.addWidget(divider)

            # Player row
            player_row = QWidget()
            player_layout = QHBoxLayout(player_row)
            player_layout.setSpacing(15)
            player_layout.setContentsMargins(0, 0, 0, 0)
            player_layout.addStretch()

            for player_name, info in players.items():
                rank = info["rank"]
                points = info["points"]
                inactive = rank is None or points == 0

                player = {"player": player_name, "rank": rank, "points": points}
                tile = self._build_player_tile(player, IMAGE_SIZE, rank, enable_tooltip=True, enable_glow=False)

                if inactive:
                    image_label = tile.layout().itemAt(0).widget()
                    effect = QGraphicsColorizeEffect()
                    effect.setColor(QColor("gray"))
                    effect.setStrength(1.0)
                    image_label.setGraphicsEffect(effect)

                tile.layout().addWidget(self._make_centered_label(self._format_rank_text(rank, points), font_size=10, bold=True))
                player_layout.addWidget(tile)
                player_layout.addStretch()

            block_layout.addWidget(player_row)
            outer_layout.addWidget(block)

        outer_layout.addStretch()

        scroll = QScrollArea()
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(outer)
        return scroll

    def _build_player_tile(self, player, image_size, rank, enable_tooltip=True, enable_glow=True):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        image = QLabel()
        image.setFixedSize(image_size, image_size)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = self._load_pixmap_from_file(
            str(ResourcePath.PLAYERS / f"{player['player']}.jpg"),
            str(ResourcePath.PLAYERS / "placeholder.png"),
        )
        image.setPixmap(
            pixmap.scaled(
                image_size, image_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        if rank in self.RANK_STYLES and enable_glow == True:
            color = self.RANK_STYLES[rank]
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(30)
            glow.setOffset(0)
            glow.setColor(QColor(color))
            image.setGraphicsEffect(glow)

        def enterEvent(event):
            QToolTip.showText(
                image.mapToGlobal(QPoint(image.width() // 2, image.height())),
                f"{player['player']}",
                image,
            )
            QWidget.enterEvent(widget, event)

        def leaveEvent(event):
            QToolTip.hideText()
            QWidget.leaveEvent(widget, event)

        if enable_tooltip:
            image.enterEvent = enterEvent
            image.leaveEvent = leaveEvent
            image.setStyleSheet(TOOLTIP_STYLESHEET_A)

        layout.addWidget(image)
        return widget

    def _format_rank_text(self, rank: int | None, points: int) -> str:
        if rank is None:
            return "Did not score"
        if 10 <= rank % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
        
        if points != 1:
            return f"{rank}{suffix} - {points} points"
        else:
            return f"{rank}{suffix} - {points} point"

    def _rank_font_size(self, rank: int) -> int:
        return int(max(20, 24 - (rank - 1) * 1.2))

    def _size_from_quantity(self, count: int) -> int:
        return min(max(80, 200 - (count - 1) * 25), 200)

    def _make_centered_label(self, text: str, bold: bool = False, font_size: int | None = None) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        if bold:
            font.setBold(True)
        if font_size is not None:
            font.setPointSize(font_size)
        label.setFont(font)
        return label

# -- BUTTON METHODS --

    def _on_event_clicked(self, event):
        event_id = event.get("id")
        if event_id not in self.event_detail_cache:
            widget = self._build_event_detail_view(event)
            self.event_detail_cache[event_id] = widget
            self.view_stack.addWidget(widget)

        self.current_detail_event_id = event_id
        self.view_stack.setCurrentWidget(self.event_detail_cache[event_id])

    def _return_to_main(self):
        self.view_stack.setCurrentWidget(self.main_page)

    def _set_active_score_button(self, root: EventDetailWidget, tab: str):
        for name, btn in root.score_state.buttons.items():
            btn.setStyleSheet(
                BUTTON_STYLESHEET_A_ACTIVE if name == tab else BUTTON_STYLESHEET_A
            )

    def _on_filter_clicked(self, root: EventDetailWidget, filter_type: str):
        state = root.score_state
        if filter_type == state.active_filter:
            return
        state.active_filter = filter_type
        self._select_score_tab(root, filter_type)

    def _select_score_tab(self, root: EventDetailWidget, tab: str):
        state = root.score_state
        self._set_active_score_button(root, tab)
        container = state.score_container

        if state.loaded[tab]:
            container.setCurrentWidget(state.widgets[tab])
            return

        container.setCurrentWidget(state.loading_widget)
        self._load_score_data(root, tab)

    def _load_score_data(self, root: EventDetailWidget, tab: str):
        state = root.score_state
        event_id = state.event.get("id")
        container = state.score_container

        tab_config = {
            "all":    (Session.event_service.get_event_standings,       (event_id,)),
            "me":     (Session.event_service.get_user_event_scores,     (Session.current_team_id, event_id)),
            "league": (Session.event_service.get_league_event_scores,   (Session.current_league_id, event_id)),
        }
        builder_config = {
            "all":    self.create_all_score_data,
            "me":     self.create_me_score_data,
            "league": self.create_league_score_data
        }

        fn, args = tab_config[tab]
        builder = builder_config[tab]

        def _success(data):
            result = builder(data)
            container.addWidget(result)
            state.widgets[tab] = result
            state.loaded[tab] = True
            if state.active_filter == tab:
                container.setCurrentWidget(result)

        def _error(e):
            error_label = QLabel(f"Failed to load data: {e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container.addWidget(error_label)
            container.setCurrentWidget(error_label)

        run_async(
            parent_widget=container,
            fn=fn,
            args=args,
            block_cursor=False,
            on_success=_success,
            on_error=_error,
        )


# LAYOUT STUFF

    def _change_event(self, delta: int):
        if not self.event_images:
            return
        self.current_event_idx = (self.current_event_idx + delta) % len(self.event_images)
        self._update_event_display()

    def _update_event_display(self):
        total = len(self.event_images)
        if total == 0:
            return

        center_idx = self.current_event_idx
        left_idx   = (center_idx - 1) % total
        right_idx  = (center_idx + 1) % total

        scale = lambda pix: pix.scaled(
            150, 150,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.center_display.setPixmap(self.event_images[center_idx].pixmap())
        self.left_preview.setPixmap(scale(self.event_images[left_idx].pixmap()))
        self.right_preview.setPixmap(scale(self.event_images[right_idx].pixmap()))

        # Labels — pull directly from event_data, no redundant dict needed
        event = self.event_data[center_idx]
        self._fit_text_to_width(self.event_name_label, event.get("name", "N/A"), 300)
        self.event_date_label.setText(
            str(datetime.fromisoformat(event.get("start_weekend", "")).date())
        )
        tier_val = event.get("tier", 0)
        self.event_tier_label.setText(
            "Tier " + str(tier_val) if tier_val > 0 else "Non-standard Tier"
        )

        self._update_next_up(center_idx=center_idx)
        self._update_timeline(str(datetime.fromisoformat(event.get("start_weekend", "")).date()))

    def _update_timeline(self, event_date_str: str):
        dt_event = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        sel_year, sel_month = dt_event.year, dt_event.month

        for i, dot in enumerate(self.timeline_dots):
            dot_year  = 2026 if i <= 9 else 2027
            dot_month = (i + 3) if i <= 9 else (i - 9)

            if dot_year == sel_year and dot_month == sel_month:
                color = "#008CFF"
            elif dot_year == self.now_year and dot_month == self.now_month:
                color = "#DA68C1"
            elif (dot_year < self.now_year) or (dot_year == self.now_year and dot_month < self.now_month):
                color = "#272727"
            else:
                color = "#646464"

            dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")

    def _update_next_up(self, center_idx: int):
        if center_idx < self.next_up_index:
            color, text = "#DB5A0F", "Past Event"
        elif center_idx == self.next_up_index:
            color, text = "#3EA702", "Next Up!"
        else:
            color, text = "#339FF8", "Future Event"

        self.next_up_label.setText(text)
        self.next_up_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: {color};
            padding: 6px 10px;
            border-radius: 8px;
        """)

    def _fit_text_to_width(self, label: QLabel, text: str, max_width: int,
                           min_font_size=2, max_font_size=40):
        """Binary-search the largest font size that fits text within max_width."""
        if not text or max_width <= 0:
            return

        font = label.font()
        font.setBold(True)
        low, high, best_size = min_font_size, max_font_size, min_font_size

        while low <= high:
            mid = (low + high) // 2
            font.setPointSize(mid)
            if QFontMetrics(font).boundingRect(text).width() <= max_width:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1

        font.setPointSize(best_size)
        label.setFont(font)
        label.setText(text)

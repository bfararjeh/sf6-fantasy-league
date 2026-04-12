from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRunnable, Qt, QThreadPool
from PyQt6.QtGui import QColor, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsColorizeEffect,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.async_runner import run_async
from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager
from app.client.theme import *
from app.client.widgets.hover_image import HoverImage
from app.client.widgets.misc import _build_empty_label, fit_text_to_width
from app.client.widgets.spinner import SpinnerWidget


# dedicated class and widget for event detail view
@dataclass
class ScoreState:
    event: dict
    score_container: QStackedWidget
    loading_widget: QWidget
    spinner: SpinnerWidget
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

        self.event_data = Session.event_data
        self.event_detail_cache = {}
        self.current_detail_event_id = None
        self._image_cache: dict[int, QImage] = {}   # built off main thread
        self._pixmap_cache: dict[int, QPixmap] = {}  # converted on main thread

        self.RANK_STYLES = {
            1: "#FFD700",
            2: "#C0C0C0",
            3: "#CD7F32",
        }

        now = datetime.now(timezone.utc)
        self.now_year, self.now_month = now.year, now.month

        self.current_event_idx = next(
            (i for i, item in enumerate(self.event_data)
             if datetime.fromisoformat(item["start_weekend"]) > now),
            len(self.event_data) - 1
        )

        self.next_up_index = self.current_event_idx

        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.view_stack = QStackedWidget()

        self.main_page = QWidget()
        self.content_layout = QVBoxLayout(self.main_page)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 15, 50, 15)
        self.content_layout.setSpacing(0)

        self.view_stack.addWidget(self.main_page)

        self.root_layout.addWidget(self.view_stack, stretch=1)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        info_widget = self._build_info()
        self.timeline_widget = self._build_timeline()
        self.next_up_label = QLabel()
        self.next_up_label.setFixedWidth(200)
        self.next_up_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.content_layout.addWidget(info_widget)
        self.content_layout.addWidget(self._build_search_bar())
        self.content_layout.addStretch()
        self.content_layout.addWidget(self._build_carousel())
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.next_up_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch()
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.timeline_widget)
        self.content_layout.addStretch()


# -- MAIN BUILDERS --

    def _build_info(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        events = QLabel("CPT Season XIII")
        events.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events.setStyleSheet("font-size: 64px; font-weight: bold;")

        layout.addWidget(events)

        qualified = QPushButton("Qualified")
        qualified.setCursor(Qt.CursorShape.PointingHandCursor)
        qualified.clicked.connect(self.app.show_qualified_view)
        qualified.setStyleSheet(BUTTON_STYLESHEET_A)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(events, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 10, 0)
        right_layout.addStretch()
        right_layout.addWidget(qualified, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        return container

    def _build_search_bar(self):
        mainC = QWidget()
        mainL = QVBoxLayout(mainC)
        mainL.setContentsMargins(0, 0, 0, 0)
        mainL.setSpacing(6)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(8)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search events...")
        self._search_input.setFixedWidth(300)
        self._search_input.setFixedHeight(34)
        self._search_input.setStyleSheet("""
            QLineEdit {
                background-color: #090E2B;
                color: #FFFFFF;
                border: 2px solid #2A3380;
                border-radius: 8px;
                padding: 0 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4200FF;
            }
        """)
        self._search_input.returnPressed.connect(self._search_event)

        search_btn = QPushButton("Go")
        search_btn.setFixedHeight(34)
        search_btn.setFixedWidth(100)
        search_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        search_btn.clicked.connect(self._search_event)

        row_layout.addStretch()
        row_layout.addWidget(self._search_input)
        row_layout.addWidget(search_btn)
        row_layout.addStretch()

        # Chips row — always visible to keep layout stable, populated on search
        self._chips_row = QWidget()
        self._chips_row.setFixedHeight(36)
        chips_layout = QHBoxLayout(self._chips_row)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(8)
        chips_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mainL.addWidget(row)
        mainL.addWidget(self._chips_row)

        return mainC

    def _search_event(self):
        query = self._search_input.text().strip().lower()
        if not query:
            self._clear_chips()
            return

        matches = [i for i, e in enumerate(self.event_data) if query in e.get("name", "").lower()]

        if not matches:
            self._clear_chips()
            self._show_chips([])   # reuse to display "no match" chip
            return

        if len(matches) == 1:
            self._clear_chips()
            self._jump_to_event(matches[0])
            return

        # Multiple matches — show chips for every one, highlight current if present
        self._show_chips(matches)

    def _show_chips(self, matches: list[int]):
        layout = self._chips_row.layout()

        # Remove old chips
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not matches:
            no_match = QLabel("No match found.")
            no_match.setStyleSheet("font-size: 12px; color: #888888;")
            layout.addWidget(no_match)
            return

        visible, overflow = matches[:6], matches[6:]

        for idx in visible:
            name = self.event_data[idx].get("name", "?")
            display_name = name[:15] + "…" if len(name) > 15 else name
            btn = QPushButton(display_name)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_current = idx == self.current_event_idx
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#4200FF" if is_current else "#1A1F4D"};
                    color: #FFFFFF;
                    border: 1px solid {"#7755FF" if is_current else "#2A3380"};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #2A1D7A;
                    border-color: #7755FF;
                }}
            """)
            btn.clicked.connect(lambda _, i=idx: self._on_chip_clicked(i))
            self._prewarm_pixmap(idx)
            layout.addWidget(btn)

        if overflow:
            more = QLabel(f"+ {len(overflow)} more")
            more.setStyleSheet("font-size: 12px; color: #555555;")
            layout.addWidget(more)

    def _clear_chips(self):
        layout = self._chips_row.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_chip_clicked(self, idx: int):
        self._clear_chips()
        self._search_input.clear()
        self._jump_to_event(idx)

    def _jump_to_event(self, idx: int):
        if idx == self.current_event_idx:
            return
        self._prewarm_pixmap(idx)
        self._delta = 1 if idx > self.current_event_idx else -1
        self._search_target_idx = idx
        clip_w = self._center_clip.width()
        end_x = -clip_w if self._delta > 0 else clip_w

        if hasattr(self, "_slide_anim") and self._slide_anim.state() == QPropertyAnimation.State.Running:
            return

        self._slide_anim = QPropertyAnimation(self.center_container, b"pos")
        self._slide_anim.setDuration(150)
        self._slide_anim.setStartValue(QPoint(0, 0))
        self._slide_anim.setEndValue(QPoint(end_x, 0))
        self._slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._slide_anim.finished.connect(self._swap_and_slide_in)
        self._slide_anim.start()
        SoundManager.play("button")

    def _build_carousel(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.left_arrow = self._make_arrow_button("arrow_left.svg", lambda: self._change_event(-1))
        self.right_arrow = self._make_arrow_button("arrow_right.svg", lambda: self._change_event(1))

        # Clipping container — card slides inside without overflow
        CLIP_W, CLIP_H = 700, 320
        self._center_clip = QWidget()
        self._center_clip.setFixedSize(CLIP_W, CLIP_H)
        self._center_clip.setStyleSheet("background: transparent;")

        self.center_container = QWidget(self._center_clip)
        self.center_container.setFixedSize(CLIP_W, CLIP_H)
        self.center_container.move(0, 0)
        self.center_container.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_container.mousePressEvent = lambda _: self._on_event_clicked(
            self.event_data[self.current_event_idx]
        )
        self.center_container.setStyleSheet("""
            QWidget {
                background-color: #090E2B;
                border: 2px solid #FFFFFF;
                border-radius: 12px;
            }
        """)

        card_layout = QHBoxLayout(self.center_container)
        card_layout.setContentsMargins(40, 30, 30, 30)
        card_layout.setSpacing(30)

        # Left side: text info
        info_widget = QWidget()
        info_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(12)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.event_name_label = QLabel("")
        self.event_name_label.setWordWrap(True)
        self.event_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.event_name_label.setStyleSheet("font-weight: bold; font-size: 26px; background: transparent; border: none;")

        self.event_date_label = QLabel("")
        self.event_date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.event_date_label.setStyleSheet("font-size: 18px; color: #AAAAAA; background: transparent; border: none;")

        self.event_tier_label = QLabel("")
        self.event_tier_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.event_tier_label.setStyleSheet("font-size: 16px; color: #666666; background: transparent; border: none;")

        hint_label = QLabel("Click to view details →")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hint_label.setStyleSheet("font-size: 13px; color: #FFFFFF; background: transparent; border: none;")

        info_layout.addWidget(self.event_name_label)
        info_layout.addWidget(self.event_date_label)
        info_layout.addWidget(self.event_tier_label)
        info_layout.addStretch()
        info_layout.addWidget(hint_label)

        # Right side: image
        self.center_display = QLabel()
        self.center_display.setFixedSize(260, 260)
        self.center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_display.setStyleSheet("background: transparent; border: none;")

        card_layout.addWidget(info_widget, stretch=1)
        card_layout.addWidget(self.center_display)

        layout.addWidget(self.left_arrow)
        layout.addWidget(self._center_clip)
        layout.addWidget(self.right_arrow)

        if self.event_data:
            self._update_event_display()
            self._prewarm_all()

        return container

    def _build_timeline(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        month_names = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

        self.timeline_dots = []
        self.timeline_labels = []

        dots_row = QWidget()
        dots_layout = QHBoxLayout(dots_row)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setSpacing(0)
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_year = 2013 + Session.SEASON

        for i, month in enumerate(month_names):
            total_months = 3 + i
            dot_year  = start_year + (total_months - 1) // 12
            dot_month = ((total_months - 1) % 12) + 1

            event_idx = next(
                (j for j, e in enumerate(self.event_data)
                 if datetime.fromisoformat(e["start_weekend"]).month == dot_month
                 and datetime.fromisoformat(e["start_weekend"]).year == dot_year),
                None,
            )

            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet("background-color: #444; border-radius: 2px;")
            self.timeline_dots.append(dot)

            dot_wrapper = QWidget()
            dot_wrapper.setFixedWidth(40)
            dot_wrapper_layout = QHBoxLayout(dot_wrapper)
            dot_wrapper_layout.setContentsMargins(0, 0, 0, 0)
            dot_wrapper_layout.setSpacing(0)
            dot_wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot_wrapper_layout.addWidget(dot)
            dots_layout.addWidget(dot_wrapper)

            if event_idx is not None:
                dot_wrapper.setCursor(Qt.CursorShape.PointingHandCursor)
                dot_wrapper.mousePressEvent = lambda _, idx=event_idx: self._jump_to_event(idx)

            if i < len(month_names) - 1:
                line = QWidget()
                line.setFixedSize(40, 2)
                line.setStyleSheet("background-color: #333;")
                dots_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignVCenter)

        labels_row = QWidget()
        labels_layout = QHBoxLayout(labels_row)
        labels_layout.setContentsMargins(0, 0, 0, 0)
        labels_layout.setSpacing(0)
        labels_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for i, month in enumerate(month_names):
            total_months = 3 + i
            dot_year  = start_year + (total_months - 1) // 12
            dot_month = ((total_months - 1) % 12) + 1

            event_idx = next(
                (j for j, e in enumerate(self.event_data)
                 if datetime.fromisoformat(e["start_weekend"]).month == dot_month
                 and datetime.fromisoformat(e["start_weekend"]).year == dot_year),
                None,
            )

            label = QLabel(month)
            label.setFixedWidth(40)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 12px; color: #AAAAAA; font-weight: bold;")
            self.timeline_labels.append(label)
            labels_layout.addWidget(label)

            if event_idx is not None:
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.mousePressEvent = lambda _, idx=event_idx: self._jump_to_event(idx)

            if i < len(month_names) - 1:
                spacer = QWidget()
                spacer.setFixedWidth(40)
                labels_layout.addWidget(spacer)

        layout.addWidget(dots_row)
        layout.addWidget(labels_row)
        return container


# -- DETAIL BUILDERS --

    def _build_event_detail_view(self, event) -> EventDetailWidget:
        # -- LEFT SIDE --
        left = QWidget()
        left_layout = QVBoxLayout(left)

        back_btn = QPushButton("Back")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(BUTTON_STYLESHEET_E)
        back_btn.clicked.connect(self._return_to_main)

        image = self._build_event_image(event, size=300)

        name = QLabel()
        fit_text_to_width(name, str(event.get("name", "N/A")), 250)

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

        spinner = SpinnerWidget(size=32, color="#4200FF")
        loading_label = QWidget()
        loading_layout = QVBoxLayout(loading_label)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.addStretch()
        loading_layout.addWidget(spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addStretch()

        empty_label = _build_empty_label()

        score_container.addWidget(empty_label)
        score_container.addWidget(loading_label)

        right_layout.addLayout(btn_row)
        right_layout.addWidget(score_container, stretch=1)

        # assemble root widget with state
        state = ScoreState(
            event=event,
            score_container=score_container,
            loading_widget=loading_label,
            spinner=spinner,
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

        ranks: dict[int, list] = {}
        for entry in data:
            ranks.setdefault(entry["rank"], []).append(entry)           # group entries by rank

        MAX_PER_ROW = 4

        for rank in sorted(ranks.keys()):
            players = ranks[rank]

            rank_block = QWidget()
            rank_block.setObjectName("rankBlock")
            rank_block.setStyleSheet("""
                QWidget#rankBlock {
                    background-color: #090E2B;
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)
            rank_block_layout = QVBoxLayout(rank_block)
            rank_block_layout.setSpacing(20)
            rank_block_layout.setContentsMargins(0, 10, 0, 20)

            rank_label = QLabel(self._format_rank_text(rank, players[0].get("points", 0)))
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            font = rank_label.font()
            font.setBold(True)
            font.setPointSize(int(max(20, 24 - (rank - 1) * 1.2)))          # font size relative to rank
            rank_label.setFont(font)

            rank_block_layout.addWidget(rank_label)

            for i in range(0, len(players), MAX_PER_ROW):
                chunk = players[i:i + MAX_PER_ROW]
                image_size = min(max(80, 200 - (len(chunk) - 1) * 25), 200)             # image size relative to number on row

                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setSpacing(15)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addStretch()
                for player in chunk:
                    extra_padding = 20 if rank <= 3 else 0
                    player_image = self._build_player_tile(player, image_size, rank, extra_padding=extra_padding)
                    row_layout.addWidget(player_image)

                row_layout.addStretch()
                rank_block_layout.addWidget(row_widget)

            QApplication.processEvents()
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
            empty = QLabel("No active team found for this event.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer_layout.addWidget(empty)
            return outer

        IMAGE_SIZE = 125
        row_widget = QWidget()
        row_widget.setObjectName("rowWidget")
        row_widget.setStyleSheet("""
            QWidget#rowWidget {
                background-color: #090E2B;
                border: 2px solid #444444;
                border-radius: 4px;
            }
        """)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(30)
        row_layout.setContentsMargins(0, 20, 0, 20)
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

        # total points summary
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
            empty = QLabel("No active teams found for this event.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return empty

        IMAGE_SIZE = 100

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

            # member block
            block = QWidget()
            block.setObjectName("block")
            block.setStyleSheet("""
                QWidget#block {
                    background-color: #090E2B;
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(15, 15, 15, 15)
            block_layout.setSpacing(10)

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

            divider = QWidget()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #333333;")
            block_layout.addWidget(divider)

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

    def _build_player_tile(self, player, image_size, rank, enable_tooltip=True, enable_glow=True, extra_padding=0):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(0, extra_padding, 0, extra_padding)

        pixmap = Session.get_pixmap("players", player["player"])
        image = HoverImage(pixmap, size=image_size)
            
        if rank in self.RANK_STYLES and enable_glow:
            color = self.RANK_STYLES[rank]
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(35)
            glow.setOffset(0)
            glow.setColor(QColor(color))
            widget.setGraphicsEffect(glow)

        _original_enter = image.enterEvent
        _original_leave = image.leaveEvent

        def enterEvent(event):
            QToolTip.showText(
                image.mapToGlobal(QPoint(image.width() // 2, image.height())),
                f"{player['player']}",
                image,
            )
            _original_enter(event)

        def leaveEvent(event):
            QToolTip.hideText()
            _original_leave(event)

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
        SoundManager.play("loaded")

    def _return_to_main(self):
        self.view_stack.setCurrentWidget(self.main_page)
        SoundManager.play("error")

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
        SoundManager.play("button")

    def _select_score_tab(self, root: EventDetailWidget, tab: str):
        state = root.score_state
        self._set_active_score_button(root, tab)
        container = state.score_container

        if state.loaded[tab]:
            container.setCurrentWidget(state.widgets[tab])
            return

        container.setCurrentWidget(state.loading_widget)
        state.spinner.start()
        self._load_score_data(root, tab)

    def _load_score_data(self, root: EventDetailWidget, tab: str):
        state = root.score_state
        event_id = state.event.get("id")
        container = state.score_container

        team_id   = Session.team_data.get("team_id")     if Session.team_data   else None
        league_id = Session.league_data.get("league_id") if Session.league_data else None

        tab_config = {
            "all":    (Session.event_service.get_event_standings,       (event_id,)),
            "me":     (Session.event_service.get_user_event_scores,     (team_id,   event_id)),
            "league": (Session.event_service.get_league_event_scores,   (league_id, event_id)),
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
            state.spinner.stop()

        def _error(e):
            error_label = QLabel(f"Failed to load data: {e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container.addWidget(error_label)
            container.setCurrentWidget(error_label)
            state.spinner.stop()

        if (tab == "me" and team_id is None) or (tab == "league" and league_id is None):
            _success(None)
            return

        run_async(
            parent_widget=container,
            fn=fn,
            args=args,
            block_cursor=False,
            on_success=_success,
            on_error=_error,
        )


# -- LAYOUT STUFF --

    def _change_event(self, delta: int):
        if not self.event_data:
            return
        # Block rapid clicks while animating
        if hasattr(self, "_slide_anim") and self._slide_anim.state() == QPropertyAnimation.State.Running:
            return

        self._delta = delta
        self._search_target_idx = None
        clip_w = self._center_clip.width()

        # Scale the incoming pixmap off the main thread so it's ready in cache
        # by the time the slide-out finishes; no UI freeze on first load
        next_idx = (self.current_event_idx + delta) % len(self.event_data)
        self._prewarm_pixmap(next_idx)

        end_x = -clip_w if delta > 0 else clip_w

        self._slide_anim = QPropertyAnimation(self.center_container, b"pos")
        self._slide_anim.setDuration(150)
        self._slide_anim.setStartValue(QPoint(0, 0))
        self._slide_anim.setEndValue(QPoint(end_x, 0))
        self._slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._slide_anim.finished.connect(self._swap_and_slide_in)
        self._slide_anim.start()

        SoundManager.play("button")

    def _swap_and_slide_in(self):
        if hasattr(self, "_search_target_idx") and self._search_target_idx is not None:
            self.current_event_idx = self._search_target_idx
            self._search_target_idx = None
        else:
            self.current_event_idx = (self.current_event_idx + self._delta) % len(self.event_data)
        self._update_event_display()

        clip_w = self._center_clip.width()
        # Position the incoming panel on the opposite side before sliding in
        enter_x = clip_w if self._delta > 0 else -clip_w
        self.center_container.move(enter_x, 0)

        self._slide_in = QPropertyAnimation(self.center_container, b"pos")
        self._slide_in.setDuration(150)
        self._slide_in.setStartValue(QPoint(enter_x, 0))
        self._slide_in.setEndValue(QPoint(0, 0))
        self._slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_in.start()

    def _update_event_display(self):
        total = len(self.event_data)
        if total == 0:
            return

        center_idx = self.current_event_idx

        self.center_display.setPixmap(self._get_event_pixmap(center_idx))

        event = self.event_data[center_idx]
        fit_text_to_width(self.event_name_label, event.get("name", "N/A"), 380)
        self.event_date_label.setText(
            str(datetime.fromisoformat(event.get("start_weekend", "")).date())
        )
        tier_val = event.get("tier", 0)
        self.event_tier_label.setText(
            "Tier " + str(tier_val) if tier_val > 0 else "Non-standard Tier"
        )

        self._update_next_up(center_idx=center_idx, event=event)
        self._update_timeline(str(datetime.fromisoformat(event.get("start_weekend", "")).date()))

    def _update_timeline(self, event_date_str: str):
        dt_event = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        sel_year, sel_month = dt_event.year, dt_event.month

        start_year = 2013 + Session.SEASON

        for i, dot in enumerate(self.timeline_dots):
            total_months = 3 + i
            dot_year  = start_year + (total_months - 1) // 12
            dot_month = ((total_months - 1) % 12) + 1

            if dot_year == sel_year and dot_month == sel_month:
                color = "#008CFF"
            elif dot_year == self.now_year and dot_month == self.now_month:
                color = "#f24949"
            elif (dot_year < self.now_year) or (dot_year == self.now_year and dot_month < self.now_month):
                color = "#272727"
            else:
                color = "#646464"

            dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")

    def _update_next_up(self, center_idx: int, event: dict = None):
        now = datetime.now(timezone.utc)
        start_raw = event.get("start_weekend") if event else None
        end_raw = event.get("end_date") if event else None
        if start_raw and end_raw:
            start_dt = datetime.fromisoformat(start_raw)
            end_dt = datetime.fromisoformat(end_raw)
            if start_dt <= now <= end_dt:
                color, text = "#B0131E", "Live!"
                self.next_up_label.setText(text)
                self.next_up_label.setStyleSheet(f"""
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    background-color: {color};
                    padding: 6px 10px;
                    border-radius: 8px;
                """)
                return

        if center_idx < self.next_up_index:
            color, text = "#DB5A0F", "Past Event"
        elif center_idx == self.next_up_index:
            color, text = "#3EA702", "Next Up"
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


# -- HELPERS --

    def _make_arrow_button(self, icon_filename: str, callback) -> QLabel:
        btn = QLabel()
        btn.setPixmap(QIcon(str(ResourcePath.ICONS / icon_filename)).pixmap(32, 32))
        btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(125)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        btn.mousePressEvent = lambda e: callback()
        return btn

    def _get_event_pixmap(self, idx: int, size: int = 260) -> QPixmap:
        """Return a cached QPixmap, converting from QImage if already built."""
        if idx in self._pixmap_cache:
            return self._pixmap_cache[idx]
        if idx in self._image_cache:
            pm = QPixmap.fromImage(self._image_cache[idx])
            self._pixmap_cache[idx] = pm
            return pm
        # Fallback: build synchronously if background worker hasn't finished
        self._build_image_cache(idx, size)
        pm = QPixmap.fromImage(self._image_cache[idx])
        self._pixmap_cache[idx] = pm
        return pm

    def _build_image_cache(self, idx: int, size: int = 260):
        """Fetch bytes and scale into a QImage (safe to call off main thread)."""
        event = self.event_data[idx]
        raw_bytes = event.get("image_bytes") or b""
        img = QImage()
        img.loadFromData(raw_bytes)
        self._image_cache[idx] = img.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _prewarm_pixmap(self, idx: int):
        """Kick off a background worker to fetch+scale idx if not yet cached."""
        if idx in self._image_cache or idx in self._pixmap_cache:
            return
        image_cache = self._image_cache

        class _Worker(QRunnable):
            def __init__(self, view, i):
                super().__init__()
                self._view = view
                self._i = i

            def run(self):
                if self._i not in image_cache:
                    self._view._build_image_cache(self._i)

        QThreadPool.globalInstance().start(_Worker(self, idx))

    def _prewarm_all(self):
        """Queue background workers for every event not yet in cache."""
        for idx in range(len(self.event_data)):
            self._prewarm_pixmap(idx)

    def _build_event_image(self, event, size=300):
        image = QLabel()
        pixmap = Session.get_pixmap("events", event.get("name", ""))
        image.setPixmap(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        return image

    def _view_help(self):
        SoundManager.play("button")

        dialog = QDialog(self)
        dialog.setWindowTitle("Info")
        dialog.setStyleSheet("background: #10194D;")
        dialog.setFixedSize(600, 350)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("Events")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        title.setStyleSheet("font-weight: bold; font-size: 24px")

        with open(str(ResourcePath.TEXTS / "events_help.txt"), "r") as file:
            text_list = file.read().splitlines()

        def _create_label(text):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 14px")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label

        layout.addWidget(title)
        for line in text_list:
            layout.addWidget(_create_label(line))

        dialog.exec()

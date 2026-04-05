import re
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.async_runner import run_async
from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager
from app.client.widgets.hover_image import HoverImage
from app.client.widgets.spinner import SpinnerWidget
from app.client.widgets.point_graph import PointsChart
from app.client.theme import *
from app.client.views.league_view import REGION_SVG_MAP


class PlayerView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.player_scores = Session.player_scores or []

        self.SORT_KEYS = {
            "name":   lambda p: p["name"].lower(),
            "region": lambda p: p["region"].lower(),
            "points": lambda p: -int(p["cum_points"]),
        }

        self.SORT_LABELS = {
            "name":   "Sort: Name",
            "region": "Sort: Region",
            "points": "Sort: Points"
        }

        self._all_players_sorted = []
        self._timeline_cache = {}
        self._player_widget_cache = {}  # name -> player card QWidget (built once)

        self._build_main()
        self._rebuild_players_view()

    def _build_main(self):
        # Page 0: scrollable player grid
        grid_page = QWidget()
        grid_layout = QVBoxLayout(grid_page)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 15, 50, 15)
        content_layout.setSpacing(50)

        self.player_cont = QWidget()
        self.player_layout = QVBoxLayout(self.player_cont)
        self.player_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.player_layout.setContentsMargins(0, 0, 0, 0)
        self.player_layout.setSpacing(20)

        content_layout.addWidget(self._build_title())
        content_layout.addWidget(self.player_cont)

        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        grid_scroll.setStyleSheet(SCROLL_STYLESHEET)
        grid_scroll.setWidget(content_widget)
        grid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        grid_layout.addWidget(grid_scroll, stretch=1)

        # Page 1: player detail
        self._detail_page = QWidget()
        self._detail_page_layout = QVBoxLayout(self._detail_page)
        self._detail_page_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_page_layout.setSpacing(0)

        self.root_stack = QStackedWidget()
        self.root_stack.addWidget(grid_page)
        self.root_stack.addWidget(self._detail_page)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.root_stack, stretch=1)
        self.setLayout(root_layout)

    def _build_title(self):
        info_cont = QWidget()
        info_cont.setObjectName("persistent")
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        title = QLabel("Player Pool")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 64px; font-weight: bold;")

        leaderboards_btn = QPushButton("Leaderboards")
        leaderboards_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        leaderboards_btn.clicked.connect(self.app.show_leaderboards_view)
        leaderboards_btn.setStyleSheet(BUTTON_STYLESHEET_A)

        globals_btn = QPushButton("Global Stats")
        globals_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        globals_btn.clicked.connect(self.app.show_globals_view)
        globals_btn.setStyleSheet(BUTTON_STYLESHEET_A)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch()
        right_layout.addWidget(leaderboards_btn, alignment=Qt.AlignmentFlag.AlignTop)

        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(globals_btn, alignment=Qt.AlignmentFlag.AlignTop)
        left_layout.addStretch()

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        self.current_sort_index = 0
        self.current_sort = list(self.SORT_KEYS.keys())[self.current_sort_index]

        self.sort_btn = QPushButton(self.SORT_LABELS[self.current_sort])
        self.sort_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.sort_btn.setFixedWidth(100)
        self.sort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_btn.clicked.connect(self._cycle_sort_mode)

        self._search_bar = QLineEdit()
        self._search_bar.setFixedWidth(250)
        self._search_bar.setPlaceholderText("Search players...")
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._on_search)
        self._search_bar.textChanged.connect(self._on_search_text_changed)

        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        controls_layout.addStretch()
        controls_layout.addWidget(self.sort_btn)
        controls_layout.addWidget(self._search_bar)
        controls_layout.addStretch()

        info_layout.addWidget(container)
        info_layout.addWidget(controls_row)

        return info_cont

    def _build_single_player_widget(self, player):
        name   = player["name"]
        region = player["region"]

        player_cont = QWidget()
        player_cont.setCursor(Qt.CursorShape.PointingHandCursor)
        player_cont_layout = QVBoxLayout(player_cont)
        player_cont_layout.setContentsMargins(0, 0, 0, 0)
        player_cont_layout.setSpacing(10)

        pixmap = Session.get_pixmap("players", name)
        image = HoverImage(pixmap, size=160)
        image.setStyleSheet("border: 3px solid #BBBBBB;")

        img_path = ResourcePath.FLAGS / f"{region}.png"
        if not img_path.exists():
            img_path = ResourcePath.FLAGS / "placeholder.png"

        info_label = QLabel()
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setText(
            "<div style='line-height: 1;'>"
            f"<span style='font-size:20px; font-weight: bold;;'>{name}</span><br/>"
            f"<span style='font-size:16px; color:#BBBBBB;'>{region}  </span>"
            f"<img src='{img_path}' width='18' height='12'><br/>"
            "</div>"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        player_cont_layout.addWidget(image)
        player_cont_layout.addWidget(info_label)

        player_cont.mousePressEvent = lambda e, p=player: self._show_player_detail(p)
        return player_cont

    def _build_player_row(self, player_batch):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for player in player_batch:
            layout.addWidget(self._player_widget_cache[player["name"]])
        return row

    def _rebuild_players_view(self, sort_by=None):
        if sort_by is None:
            sort_by = getattr(self, "current_sort", "name")

        self.built = True
        players = self.player_scores[:]
        players.sort(key=self.SORT_KEYS[sort_by])
        self._all_players_sorted = players

        # Build per-player widgets once — sort/search never recreates them.
        if not self._player_widget_cache:
            self._player_widget_cache = {
                p["name"]: self._build_single_player_widget(p)
                for p in players
            }

        self._render_player_list(players)

    def _render_player_list(self, players):
        # Detach all cached player widgets before tearing down rows,
        # so the HoverImage/pixmap widgets are never destroyed.
        for w in self._player_widget_cache.values():
            w.setParent(None)

        # Tear down old row shells (they're cheap; player widgets are already detached).
        while self.player_layout.count():
            item = self.player_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build fresh row shells and re-attach the cached player widgets.
        for i in range(0, len(players), 5):
            batch = players[i:i + 5]
            self.player_layout.addWidget(self._build_player_row(batch))

    def _cycle_sort_mode(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.current_sort_index = (self.current_sort_index + 1) % len(self.SORT_KEYS)
        self.current_sort = list(self.SORT_KEYS.keys())[self.current_sort_index]
        self.sort_btn.setText(self.SORT_LABELS[self.current_sort])
        self._rebuild_players_view(sort_by=self.current_sort)
        QApplication.restoreOverrideCursor()
        SoundManager.play("button")

    def _on_search_text_changed(self, text):
        self._pending_search = text
        self._search_timer.start()

    def _on_search(self):
        text = getattr(self, "_pending_search", "").strip().lower()
        if not text:
            self._render_player_list(self._all_players_sorted)
        else:
            filtered = [p for p in self._all_players_sorted if text in p["name"].lower()]
            self._render_player_list(filtered)

    def _show_player_detail(self, player):
        while self._detail_page_layout.count():
            item = self._detail_page_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        name = player["name"]

        back_btn = QPushButton("Back")
        back_btn.setFixedWidth(100)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(BUTTON_STYLESHEET_E)
        back_btn.clicked.connect(lambda: (SoundManager.play("error"), self.root_stack.setCurrentIndex(0)))

        back_bar = QWidget()
        back_bar_layout = QHBoxLayout(back_bar)
        back_bar_layout.setContentsMargins(20, 10, 20, 0)
        back_bar_layout.addWidget(back_btn)
        back_bar_layout.addStretch()

        self._detail_content = QWidget()
        self._detail_content_layout = QVBoxLayout(self._detail_content)
        self._detail_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._detail_content_layout.setContentsMargins(50, 15, 50, 15)

        if name in self._timeline_cache:
            self._detail_content_layout.addWidget(self._build_detail_card(player, self._timeline_cache[name]))
        else:
            spinner = SpinnerWidget(size=48)
            self._detail_content_layout.addStretch()
            self._detail_content_layout.addWidget(spinner, alignment=Qt.AlignmentFlag.AlignCenter)
            self._detail_content_layout.addStretch()

            def _success(timeline):
                self._timeline_cache[name] = timeline
                while self._detail_content_layout.count():
                    item = self._detail_content_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                self._detail_content_layout.addWidget(self._build_detail_card(player, timeline))
                SoundManager.play("button")

            def _error(e):
                while self._detail_content_layout.count():
                    item = self._detail_content_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                err = QLabel(f"Failed to load history: {e}")
                err.setAlignment(Qt.AlignmentFlag.AlignCenter)
                err.setStyleSheet("color: #ff8168; font-size: 14px;")
                self._detail_content_layout.addWidget(err)

            QTimer.singleShot(200, lambda: run_async(
                parent_widget=self._detail_content,
                fn=Session.event_service.get_player_points_timeline,
                args=(name,),
                block_cursor=False,
                on_success=_success,
                on_error=_error,
            ))

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        detail_scroll.setStyleSheet(SCROLL_STYLESHEET)
        detail_scroll.setWidget(self._detail_content)

        self._detail_page_layout.addWidget(detail_scroll, stretch=1)
        self._detail_page_layout.addWidget(back_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self._detail_page_layout.addSpacerItem(QSpacerItem(0, 25))

        self.root_stack.setCurrentIndex(1)

    def _build_detail_card(self, player, timeline):
        name   = player["name"]
        region = player["region"]
        points = player["cum_points"]

        default_joined = f"{2013 + Session.SEASON}-03-01T00:00:00+00:00"

        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(100, 10, 100, 15)
        layout.setSpacing(25)

        title = QLabel("Player Pool")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 64px; font-weight: bold;")

        sub = QLabel(f"Point breakdown and event history for {name}.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 14px; color: #444444;")

        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addSpacerItem(QSpacerItem(0,25))

        # portrait + name/region + world map
        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setSpacing(30)

        img_label = HoverImage(Session.get_pixmap("players", name), size=160, border_color="#FFFFFF", border_width=2)

        region_img = ResourcePath.FLAGS / f"{region}.png"
        if not region_img.exists():
            region_img = ResourcePath.FLAGS / "placeholder.png"

        info = QLabel()
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setText(
            "<div style='line-height: 1.5;'>"
            f"<span style='font-size:28px; font-weight:bold;'>{name}</span><br/>"
            f"<span style='font-size:18px; color:#BBBBBB;'>{region}  </span>"
            f"<img src='{region_img}' width='22' height='15'>"
            "</div>"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addStretch()
        left_layout.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addStretch()

        svg_bytes = self._highlight_svg(region)
        map_widget = QSvgWidget()
        map_widget.load(svg_bytes)
        svg_width = 600
        svg_height = int(svg_width * 857 / 2000)
        map_widget.setFixedSize(svg_width, svg_height)

        top_layout.addWidget(left_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(map_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

        # stats bar
        best_gained  = max((e["points_gained"] for e in timeline), default=0)
        worst_gained = min((e["points_gained"] for e in timeline), default=0)
        avg_gained   = round(points / len(timeline), 1) if timeline else 0

        stats_widget = QWidget()
        stats_widget.setStyleSheet("background-color: #090E2B; border-radius: 6px;")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(15, 12, 15, 12)
        stats_layout.setSpacing(0)

        for i, (label, value) in enumerate([
            ("Events Played",  str(len(timeline))),
            ("Total Points",   str(points)),
            ("AVG. Pts/Event", str(avg_gained)),
            ("Best Event",     f"+{best_gained}"),
            ("Worst Event",    f"+{worst_gained}"),
        ]):
            stat_col = QVBoxLayout()
            stat_col.setSpacing(2)
            stat_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 14px; color: #AAAAAA;")

            val = QLabel(value)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")

            stat_col.addWidget(lbl)
            stat_col.addWidget(val)

            stat_item = QWidget()
            stat_item.setLayout(stat_col)
            stats_layout.addWidget(stat_item, stretch=1)

            if i < 4:
                div = QFrame()
                div.setFrameShape(QFrame.Shape.VLine)
                div.setStyleSheet("color: rgba(255,255,255,30);")
                stats_layout.addWidget(div)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(255,255,255,40);")

        layout.addWidget(top)
        layout.addWidget(stats_widget)
        layout.addSpacerItem(QSpacerItem(0, 25))
        layout.addWidget(divider)
        layout.addSpacerItem(QSpacerItem(0, 25))

        if not timeline:
            empty = QLabel("No event history available.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #AAAAAA; font-size: 16px;")
            layout.addWidget(empty)
        else:
            layout.addWidget(PointsChart(timeline, joined_at=default_joined))

            tl_divider = QFrame()
            tl_divider.setFrameShape(QFrame.Shape.HLine)
            tl_divider.setStyleSheet("color: rgba(255,255,255,40);")

            tl_widget = QWidget()
            tl_layout = QGridLayout(tl_widget)
            tl_layout.setContentsMargins(25, 0, 25, 0)
            tl_layout.setVerticalSpacing(6)
            tl_layout.setHorizontalSpacing(20)
            tl_layout.setColumnStretch(0, 1)

            for i, entry in enumerate(timeline):
                name_lbl = QLabel(entry["event_name"])
                name_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")

                rank_lbl = QLabel(f"#{entry['rank']}")
                rank_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                rank_lbl.setStyleSheet("font-size: 20px;")

                date_lbl = QLabel(entry["event_date"].split("T")[0])
                date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                date_lbl.setStyleSheet("font-size: 16px; color: #888888;")

                tl_layout.addWidget(name_lbl, i, 0)
                tl_layout.addWidget(rank_lbl, i, 1)
                tl_layout.addWidget(date_lbl, i, 2)

            layout.addSpacerItem(QSpacerItem(0, 25))
            layout.addWidget(tl_divider)
            layout.addSpacerItem(QSpacerItem(0, 25))
            layout.addWidget(tl_widget)

        layout.addStretch()
        return frame

    def _highlight_svg(self, region: str) -> bytes:
        svg_path = ResourcePath.IMAGES / "world.svg"
        svg_text = svg_path.read_text(encoding="utf-8")

        mapping = REGION_SVG_MAP.get(region)
        if not mapping:
            return svg_text.encode("utf-8")

        attr, value = mapping
        pattern = rf'(<path\b[^>]*\b{attr}="{re.escape(value)}"[^>]*)(/>|>)'
        svg_text = re.sub(
            pattern,
            lambda m: m.group(0).replace(m.group(1), m.group(1) + ' style="fill:#f24949;"'),
            svg_text
        )
        return svg_text.encode("utf-8")

    @staticmethod
    def preload():
        for player in Session.player_scores or []:
            Session.get_image("players", player["name"])

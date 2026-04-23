import re
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QSpacerItem,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QGroupBox,
    QFrame,
    QSizePolicy,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QStackedWidget,
    QScrollArea,
    QGraphicsColorizeEffect,
    QListWidget,
    QListWidgetItem,
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async
from app.client.controllers.sound_manager import SoundManager
from app.client.controllers.realtime_listener import RealtimeListener
from app.client.widgets.misc import fit_text_to_width, set_status
from app.client.widgets.hover_image import HoverImage
from app.client.widgets.point_graph import PointsChart
from app.client.theme import *

from app.client.widgets.misc import REGION_SVG_MAP

class LeagueView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self._stat_cache = {}
        self._realtime_listener = None
        self._last_pick_turn_notified = None

        self.FEED_COLOURS = {
            "0": "#FFFFFF",
            "1": "#B39DDB",
            "2": "#FFD166",
            "3": "#FF6B6B",
            "4": "#7EB8F7",
            "5": "#88FF87",
            "6": "#FFA94D",
            "7": "#F783AC",
            "8": "#74C0FC",
            "9": "#888888",
        }

        self._build_static()
        self._refresh()

# -- STATIC WIDGETS --

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(30)

        # Stack switches between pre-draft and post-draft top-level layouts
        self.view_stack = QStackedWidget()
        self.no_league_page = self._build_no_league_page()
        self.pre_draft_page  = self._build_pre_draft_page()
        self.post_draft_page = self._build_post_draft_page()
        self.view_stack.addWidget(self.no_league_page)
        self.view_stack.addWidget(self.pre_draft_page)
        self.view_stack.addWidget(self.post_draft_page)

        self.root_layout.addWidget(self.view_stack, stretch=1)
        self.root_layout.addWidget(self.status_label)

        self.setLayout(self.root_layout)

    def _build_no_league_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.setContentsMargins(50, 0, 50, 0)
        page_layout.setSpacing(0)

        page_layout.addStretch()
        page_layout.addWidget(self._build_leagueless_controls())
        page_layout.addStretch()

        return page

    def _build_pre_draft_page(self):
        # history stack page indices
        self._HS_HISTORY = 0
        self._HS_OWNER   = 1
        self._HS_PICKER  = 2
        self._HS_CREATOR = 3

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # Header
        self.pre_draft_header = self._build_pre_draft_header()
        header_divider_wrapper = QWidget()
        header_divider_wrapper_layout = QHBoxLayout(header_divider_wrapper)
        header_divider_wrapper_layout.setContentsMargins(30, 0, 30, 0)
        header_divider = QFrame()
        header_divider.setFrameShape(QFrame.Shape.HLine)
        header_divider.setStyleSheet("color: #444444;")
        header_divider.setFixedHeight(2)
        header_divider_wrapper_layout.addWidget(header_divider)

        # Roster bar (full-width band, hidden when no team)
        self.team_overview = self._build_roster_overview()

        # Roster divider with horizontal padding so it doesn't touch window edges
        roster_divider_wrapper = QWidget()
        roster_divider_wrapper_layout = QHBoxLayout(roster_divider_wrapper)
        roster_divider_wrapper_layout.setContentsMargins(30, 0, 30, 0)
        self.roster_divider = QFrame()
        self.roster_divider.setFrameShape(QFrame.Shape.HLine)
        self.roster_divider.setStyleSheet("color: #444444;")
        self.roster_divider.setFixedHeight(2)
        roster_divider_wrapper_layout.addWidget(self.roster_divider)
        self._roster_divider_wrapper = roster_divider_wrapper

        # Body: history area + sidebar
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.history_area = self._build_history_area()
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("color: #444444;")
        vline.setFixedWidth(2)
        self.pre_draft_sidebar = self._build_pre_draft_sidebar()

        body_layout.addWidget(self.history_area, stretch=1)
        body_layout.addWidget(vline)
        body_layout.addWidget(self.pre_draft_sidebar)

        page_layout.addWidget(self.pre_draft_header)
        page_layout.addWidget(header_divider_wrapper)
        page_layout.addWidget(self.team_overview)
        page_layout.addWidget(self._roster_divider_wrapper)
        page_layout.addWidget(body_widget, stretch=1)

        # Keep player_stats built so self.player_detail_layout exists for post-draft use
        self.player_stats = self._build_player_stat_section()

        return page

    def _build_post_draft_page(self):
        # root page w header
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.league_header_strip = self._build_league_header_strip()
        layout.addWidget(self.league_header_strip)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #444444;")
        line.setFixedHeight(2)
        layout.addWidget(line)

        # two col team area
        team_area = QWidget()
        team_area_layout = QHBoxLayout(team_area)
        team_area_layout.setContentsMargins(0, 0, 0, 0)
        team_area_layout.setSpacing(0)

        self.active_player_column = self._build_active_player_column()
        self.stat_container = self._build_stat_container()
        self.post_draft_feed = self._build_post_draft_feed()

        self.right_panel = QStackedWidget()
        self.right_panel.addWidget(self.stat_container)   # page 0: stats
        self.right_panel.addWidget(self.post_draft_feed)  # page 1: feed + chat

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("color: #444444;")
        vline.setFixedWidth(2)

        team_area_layout.addWidget(self.active_player_column)
        team_area_layout.addWidget(vline)
        team_area_layout.addWidget(self.right_panel, stretch=1)

        layout.addWidget(team_area, stretch=1)

        return page

# -- NO LEAGUE BUILDERS --

    def _build_leagueless_controls(self):
        container = QWidget()
        container.setFixedWidth(600)
        layout = QVBoxLayout(container)
        layout.setSpacing(50)

        self.leagueless_title = QLabel("Create or Join a League!")
        self.leagueless_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leagueless_title.setStyleSheet("font-size: 32px; font-weight: bold;")

        layout.addWidget(self.leagueless_title)
        layout.addWidget(self._build_create_and_join_controls())

        return container

    def _build_create_and_join_controls(self):
        self.create_league_input = QLineEdit()
        self.create_league_input.setPlaceholderText("League Name")
        self.create_league_input.returnPressed.connect(self.create_league)

        create_group = QGroupBox("Create League")
        create_group.setStyleSheet("QGroupBox { color: white; }")
        create_group.setFixedHeight(80)
        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_league_input)
        create_group.setLayout(create_group_layout)

        create_btn = QPushButton("Create")
        create_btn.setFixedWidth(100)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.clicked.connect(self.create_league)

        create_btn_wrap = QWidget()
        create_btn_wrap_layout = QVBoxLayout(create_btn_wrap)
        create_btn_wrap_layout.setContentsMargins(0, 0, 0, 0)
        create_btn_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        create_btn_wrap_layout.addSpacerItem(QSpacerItem(0,22))
        create_btn_wrap_layout.addWidget(create_btn)

        create_row = QHBoxLayout()
        create_row.addWidget(create_group)
        create_row.addWidget(create_btn_wrap)
        create_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")
        self.join_input.returnPressed.connect(self.join_league)

        join_group = QGroupBox("Join League")
        join_group.setStyleSheet("QGroupBox { color: white; }")
        join_group.setFixedHeight(80)
        join_group_layout = QVBoxLayout()
        join_group_layout.addWidget(self.join_input)
        join_group.setLayout(join_group_layout)

        join_btn = QPushButton("Join")
        join_btn.setFixedWidth(100)
        join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        join_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        join_btn.clicked.connect(self.join_league)

        join_btn_wrap = QWidget()
        join_btn_wrap_layout = QVBoxLayout(join_btn_wrap)
        join_btn_wrap_layout.setContentsMargins(0, 0, 0, 0)
        join_btn_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        join_btn_wrap_layout.addSpacerItem(QSpacerItem(0,22))
        join_btn_wrap_layout.addWidget(join_btn)

        join_row = QHBoxLayout()
        join_row.addWidget(join_group)
        join_row.addWidget(join_btn_wrap)
        join_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setSpacing(25)
        layout.addLayout(join_row)
        layout.addLayout(create_row)
        return cont


# -- PRE DRAFT BUILDERS

    def _build_pre_draft_header(self):
        header = QWidget()
        header.setFixedHeight(84)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(20)

        self.league_name_label = QLabel("")
        self.league_name_label.setStyleSheet("font-weight: bold;")

        # Members column: "Members X/5" header + username list below
        members_col = QWidget()
        members_col_layout = QVBoxLayout(members_col)
        members_col_layout.setContentsMargins(0, 0, 0, 0)
        members_col_layout.setSpacing(2)
        members_col_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.capacity_label = QLabel("")
        self.capacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capacity_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #BBBBBB;")

        self.members_list_label = QLabel("")
        self.members_list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.members_list_label.setStyleSheet("font-size: 14px; color: #888888;")

        members_col_layout.addWidget(self.capacity_label)
        members_col_layout.addWidget(self.members_list_label)

        self.league_id_label = QLabel("")
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.league_id_label.setStyleSheet("font-size: 13px; color: #888888;")

        layout.addWidget(self.league_name_label)
        layout.addStretch()
        layout.addWidget(members_col)
        layout.addStretch()
        layout.addWidget(self.league_id_label)

        return header

    def _build_history_area(self):
        area = QWidget()
        area_layout = QVBoxLayout(area)
        area_layout.setContentsMargins(30, 10, 15, 10)
        area_layout.setSpacing(8)

        # Top row: title + owner settings button + picker toggle (during draft)
        top_row = QHBoxLayout()

        self.settings_toggle_btn = QPushButton("Settings")
        self.settings_toggle_btn.setFixedWidth(100)
        self.settings_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_toggle_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.settings_toggle_btn.setVisible(False)
        self.settings_toggle_btn.clicked.connect(self._toggle_settings)

        self.picker_toggle_btn = QPushButton("Draft")
        self.picker_toggle_btn.setFixedWidth(100)
        self.picker_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.picker_toggle_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.picker_toggle_btn.setVisible(False)
        self.picker_toggle_btn.clicked.connect(self._toggle_picker)

        top_row.addStretch()
        top_row.addWidget(self.settings_toggle_btn)
        top_row.addWidget(self.picker_toggle_btn)

        # Stack with 4 pages
        self.history_stack = QStackedWidget()

        self.history_content = self._build_history_feed()  # page 0: scrollable event feed
        self.draft_controls = self._build_owner_controls()   # page 1: owner controls
        self.pick_container = self._build_draft_picker()     # page 2: player picker
        self.team_creator_container = self._build_team_creator()  # page 3: team creator

        self.history_stack.addWidget(self.history_content)
        self.history_stack.addWidget(self.draft_controls)
        self.history_stack.addWidget(self.pick_container)
        self.history_stack.addWidget(self.team_creator_container)

        # Chat input row
        chat_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Send a message...")
        self.chat_input.setMaxLength(128)
        self.chat_input.returnPressed.connect(self._send_chat)
        self.chat_send_btn = QPushButton("Send")
        self.chat_send_btn.setFixedWidth(70)
        self.chat_send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_send_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.chat_send_btn.clicked.connect(self._send_chat)
        chat_row.addWidget(self.chat_input)
        chat_row.addWidget(self.chat_send_btn)

        area_layout.addLayout(top_row)
        area_layout.addWidget(self.history_stack, stretch=1)
        area_layout.addLayout(chat_row)

        return area

    def _build_pre_draft_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        draft_order_hdr = QLabel("Draft Order:")
        draft_order_hdr.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")

        self.draft_order_label = QLabel("N/A")
        self.draft_order_label.setWordWrap(True)
        self.draft_order_label.setStyleSheet("font-size: 14px; color: #CCCCCC;")

        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.HLine)
        div1.setStyleSheet("color: #444444;")

        forfeit_hdr = QLabel("Forfeit:")
        forfeit_hdr.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")

        self.forfeit_label = QLabel("")
        self.forfeit_label.setWordWrap(True)
        self.forfeit_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff8168;")

        # Next pick avatar slot (draft phase) — sized to fit snug inside 220px sidebar with 15px margins each side
        avatar_size = 90
        self.next_pick_avatar_slot = QWidget()
        self.next_pick_avatar_slot.setFixedSize(avatar_size, avatar_size)
        self.next_pick_avatar_slot_layout = QVBoxLayout(self.next_pick_avatar_slot)
        self.next_pick_avatar_slot_layout.setContentsMargins(0, 0, 0, 0)
        self.next_pick_avatar_slot.setVisible(False)

        self.next_pick_label = QLabel("N/A")
        self.next_pick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_pick_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #88ff87;")
        self.next_pick_label.setVisible(False)

        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("color: #444444;")

        self.leave_btn = QPushButton("Leave League")
        self.leave_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.leave_btn.setStyleSheet(BUTTON_STYLESHEET_E)
        self.leave_btn.clicked.connect(self.leave_league)

        layout.addWidget(draft_order_hdr)
        layout.addWidget(self.draft_order_label)
        layout.addWidget(div1)
        layout.addWidget(forfeit_hdr)
        layout.addWidget(self.forfeit_label)
        layout.addStretch()
        layout.addWidget(self.next_pick_avatar_slot, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.next_pick_label)
        layout.addWidget(div2)
        layout.addWidget(self.leave_btn)

        return sidebar

    def _build_history_feed(self):
        # Outer scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(SCROLL_STYLESHEET)

        # Inner container — rows appended by _update_history_feed
        self._history_feed_container = QWidget()
        self._history_feed_layout = QVBoxLayout(self._history_feed_container)
        self._history_feed_layout.setContentsMargins(0, 4, 0, 4)
        self._history_feed_layout.setSpacing(0)
        self._history_feed_layout.addStretch()

        scroll.setWidget(self._history_feed_container)
        return scroll

    def _uid_to_name(self, uid):
        for m in (self.my_leaguemates_raw or []):
            if str(m.get("user_id", "")) == str(uid):
                return m.get("manager_name", "Unknown")
        return "Unknown"

    def _format_league_msg(self, message):
        parts = message.split("|")
        html = ""
        for part in parts:
            if not part:
                continue
            if part[0] not in self.FEED_COLOURS:
                html += part
                continue
            color = self.FEED_COLOURS[part[0]]
            rest  = part[1:]
            bracket_match = re.match(r'^\[([^\]]*)\](.*)', rest, re.DOTALL)
            if bracket_match:
                inner = bracket_match.group(1)
                if re.search(r'[a-f0-9-]{36}', inner):
                    uuids = re.findall(r'"([a-f0-9-]{36})"', inner)
                    names = ", ".join(
                        f"<span style='color:{color};'>{self._uid_to_name(u)}</span>"
                        for u in uuids
                    )
                    html += names + bracket_match.group(2)
                else:
                    html += f"<span style='color:{color};'>{inner}</span>" + bracket_match.group(2)
            else:
                space = rest.find(" ")
                if space == -1:
                    html += f"<span style='color:{color};'>{rest}</span>"
                else:
                    html += f"<span style='color:{color};'>{rest[:space]}</span>{rest[space:]}"
        return html

    def _build_feed_row(self, html, ts_str):
        """Build a single styled feed row widget."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 10, 8, 10)
        row_layout.setSpacing(8)

        bullet = QLabel("•")
        bullet.setStyleSheet("font-size: 18px; color: #555555;")
        bullet.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        msg_label = QLabel(f"<span style='font-size:18px; color:#888888;'>{html}</span>")
        msg_label.setTextFormat(Qt.TextFormat.RichText)
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        ts_label = QLabel(ts_str)
        ts_label.setStyleSheet("font-size: 12px; color: #555555;")
        ts_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ts_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        row_layout.addWidget(bullet, alignment=Qt.AlignmentFlag.AlignTop)
        row_layout.addWidget(msg_label)
        row_layout.addWidget(ts_label, alignment=Qt.AlignmentFlag.AlignTop)
        return row

    def _merge_feed_events(self):
        """Return sorted (ts, html) pairs from history + chat."""
        from datetime import datetime, timezone
        events = []
        for entry in (self.my_league_history or []):
            events.append((entry.get("created_at", ""), self._format_league_msg(entry.get("message", ""))))
        for entry in (self.my_league_chat or []):
            sender = entry.get("sender", "")
            msg    = entry.get("message", "")
            html   = f"<span style='color:{self.FEED_COLOURS['1']};'>{sender}:</span> <span style='color:#FFFFFF;'>{msg}</span>"
            events.append((entry.get("created_at", ""), html))
        events.sort(key=lambda e: e[0], reverse=True)
        return events

    def _update_history_feed(self):
        from datetime import datetime, timezone

        while self._history_feed_layout.count() > 1:
            item = self._history_feed_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for ts, html in self._merge_feed_events():
            try:
                ts_str = datetime.fromisoformat(ts).astimezone(timezone.utc).strftime("%b %d, %H:%M")
            except Exception:
                ts_str = ts[:16] if ts else ""
            self._history_feed_layout.insertWidget(
                self._history_feed_layout.count() - 1,
                self._build_feed_row(html, ts_str)
            )

    def _build_owner_controls(self):
        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Alice, Bob, Charlie")
        self.draft_input.returnPressed.connect(self.assign_draft_order)

        title = QLabel("Owner Controls")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")

        group = QGroupBox("Assign Draft Order")
        group.setStyleSheet("QGroupBox { color: white; }")
        group.setMaximumHeight(120)
        group_layout = QHBoxLayout()
        group_layout.addWidget(self.draft_input)
        group.setLayout(group_layout)

        set_btn = QPushButton("Set Order")
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        set_btn.setFixedWidth(100)
        set_btn.clicked.connect(self.assign_draft_order)

        begin_btn = QPushButton("Begin Draft")
        begin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        begin_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        begin_btn.setFixedWidth(100)
        begin_btn.clicked.connect(self.begin_draft)

        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Loser must...")
        self.forfeit_input.returnPressed.connect(self.set_forfeit)

        forfeit_group = QGroupBox("Set Forfeit")
        forfeit_group.setStyleSheet("QGroupBox { color: white; }")
        forfeit_group.setMaximumHeight(120)
        forfeit_group_layout = QVBoxLayout()
        forfeit_group_layout.addWidget(self.forfeit_input)
        forfeit_group.setLayout(forfeit_group_layout)

        forfeit_btn = QPushButton("Submit")
        forfeit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forfeit_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        forfeit_btn.setFixedWidth(100)
        forfeit_btn.clicked.connect(self.set_forfeit)

        cont = QWidget()
        cont_layout = QVBoxLayout(cont)
        cont_layout.setSpacing(15)
        cont_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cont_layout.setContentsMargins(80, 20, 80, 20)

        set_btn_wrap = QWidget()
        set_btn_wrap_layout = QVBoxLayout(set_btn_wrap)
        set_btn_wrap_layout.setContentsMargins(0, 0, 0, 0)
        set_btn_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        set_btn_wrap_layout.addSpacerItem(QSpacerItem(0,24))
        set_btn_wrap_layout.addWidget(set_btn)

        begin_btn_wrap = QWidget()
        begin_btn_wrap_layout = QVBoxLayout(begin_btn_wrap)
        begin_btn_wrap_layout.setContentsMargins(0, 0, 0, 0)
        begin_btn_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        begin_btn_wrap_layout.addSpacerItem(QSpacerItem(0,22))          # ugly but works lmao
        begin_btn_wrap_layout.addWidget(begin_btn)

        row = QHBoxLayout()
        row.addWidget(group)
        row.addWidget(set_btn_wrap)
        row.addWidget(begin_btn_wrap)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        forfeit_btn_wrap = QWidget()
        forfeit_btn_wrap_layout = QVBoxLayout(forfeit_btn_wrap)
        forfeit_btn_wrap_layout.setContentsMargins(0, 0, 0, 0)
        forfeit_btn_wrap_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        forfeit_btn_wrap_layout.addSpacerItem(QSpacerItem(0,24))
        forfeit_btn_wrap_layout.addWidget(forfeit_btn)

        forfeit_row = QHBoxLayout()
        forfeit_row.addWidget(forfeit_group)
        forfeit_row.addWidget(forfeit_btn_wrap)
        forfeit_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        cont_layout.addWidget(title)
        cont_layout.addLayout(row)
        cont_layout.addLayout(forfeit_row)

        self.draft_controls = cont
        return cont

    def _build_team_creator(self):
        self.team_creator_container = QWidget()
        layout = QVBoxLayout(self.team_creator_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(80, 20, 80, 20)

        self.create_team_input = QLineEdit()
        self.create_team_input.setPlaceholderText("My Team...")
        self.create_team_input.returnPressed.connect(self.create_team)

        create_group = QGroupBox("")
        create_group.setStyleSheet("QGroupBox { color: white; }")
        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_team_input)
        create_group.setLayout(create_group_layout)

        create_label = QLabel("Name your team!")
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        create_btn = QPushButton("Submit")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.setFixedWidth(100)
        create_btn.clicked.connect(self.create_team)

        create_layout = QHBoxLayout()
        create_layout.addWidget(create_group, stretch=1)
        create_layout.addWidget(create_btn)
        create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(create_label)
        layout.addSpacing(10)
        layout.addLayout(create_layout)
        return self.team_creator_container

    def _build_draft_picker(self):
        self.pick_container = QWidget()
        outer = QVBoxLayout(self.pick_container)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(40, 20, 40, 20)
        outer.setSpacing(18)

        label = QLabel("It's your turn to pick a player!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        # -- left: search + list --
        self.pick_search = QLineEdit()
        self.pick_search.setPlaceholderText("Search players...")
        self.pick_search.setFixedWidth(220)

        self.pick_list = QListWidget()
        self.pick_list.setFixedSize(220, 160)
        self.pick_list.setStyleSheet("""
            QListWidget {
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #ad9665;
            }
        """)
        self.pick_list.itemClicked.connect(self._on_pick_list_select)

        self._pick_preview_timer = QTimer()
        self._pick_preview_timer.setSingleShot(True)
        self._pick_preview_timer.setInterval(75)
        self._pick_preview_timer.timeout.connect(self._do_pick_preview_update)
        self.pick_search.textChanged.connect(self._on_pick_search_changed)
        self.pick_search.returnPressed.connect(self.pick_player)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self.pick_list)

        btn = QPushButton("Pick")
        btn.setFixedWidth(100)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BUTTON_STYLESHEET_A)
        btn.clicked.connect(self.pick_player)

        # -- right: player image --
        self._pick_preview_pixmap = Session.get_pixmap("players", "")
        self._pick_pixmap_cache = {}
        self.pick_preview_image = HoverImage(
            self._pick_preview_pixmap, size=160, border_width=2, border_color="#BBBBBB"
        )

        row = QHBoxLayout()
        row.setSpacing(24)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addStretch()
        row.addWidget(left, alignment=Qt.AlignmentFlag.AlignTop)
        row.addWidget(self.pick_preview_image, alignment=Qt.AlignmentFlag.AlignCenter)
        row.addStretch()

        outer.addWidget(label)
        outer.addWidget(self.pick_search, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addLayout(row)
        outer.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        return self.pick_container

    def _refresh_pick_input(self):
        self._all_pick_names = sorted(
            [p["name"] for p in (Session.player_scores or [])], key=str.casefold
        )
        self._populate_pick_list(self._all_pick_names)

    def _populate_pick_list(self, names):
        self.pick_list.blockSignals(True)
        self.pick_list.clear()
        for name in names:
            self.pick_list.addItem(QListWidgetItem(name))
        self.pick_list.blockSignals(False)

    def _build_roster_overview(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)

        self.team_name_label = QLabel("")
        self.team_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.team_name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")

        self.team_bar_layout = QHBoxLayout()
        self.team_bar_layout.setSpacing(4)

        slots_row = QHBoxLayout()
        slots_row.addStretch()
        slots_row.addLayout(self.team_bar_layout)
        slots_row.addStretch()

        layout.addWidget(self.team_name_label)
        layout.addLayout(slots_row)
        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(5)

        image = QLabel()
        image.setFixedSize(QSize(85, 85))
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        if player:
            player_name = player.get("id", "-")

            pixmap = Session.get_pixmap("players", player_name)
            image = HoverImage(pixmap, size=85, border_width=2, border_color="#BBBBBB")
        else:
            image.setStyleSheet("border: 2px dashed #555; background-color: #333; color: #eee;")
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setText("?")

        layout.addWidget(image)
        return slot

    def _build_player_stat_section(self):
        container = QWidget()
        self.player_detail_layout = QVBoxLayout(container)
        self.player_detail_layout.setContentsMargins(50, 0, 50, 0)
        self.player_detail_layout.setSpacing(15)
        return container


# -- POST DRAFT BUILDERS --

    def _build_league_header_strip(self):
        strip = QWidget()
        strip.setFixedHeight(60)
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setSpacing(40)

        self.strip_league_name   = QLabel("")
        self.strip_members_label = QLabel("")
        self.strip_forfeit_label = QLabel("")

        self.strip_league_name.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.strip_members_label.setStyleSheet("font-size: 13px; color: #BBBBBB;")
        self.strip_forfeit_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff8168;")

        self.feed_toggle_btn = QPushButton("Feed")
        self.feed_toggle_btn.setFixedWidth(80)
        self.feed_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.feed_toggle_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.feed_toggle_btn.clicked.connect(self._toggle_post_draft_feed)

        layout.addWidget(self.strip_league_name)
        layout.addWidget(self.strip_members_label)
        layout.addStretch()
        layout.addWidget(self.strip_forfeit_label)
        layout.addWidget(self.feed_toggle_btn)

        return strip

    def _build_active_player_column(self):
        # main cont
        column_inner = QWidget()
        layout = QVBoxLayout(column_inner)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # active layoout
        self.active_portrait_layout = QVBoxLayout()
        self.active_portrait_layout.setSpacing(10)
        self.active_portrait_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # former toggle
        self.former_toggle_btn = QPushButton("▼ Former")
        self.former_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.former_toggle_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.former_toggle_btn.clicked.connect(self.toggle_former_players)

        # former layout
        self.former_section = QWidget()
        self.former_portrait_layout = QVBoxLayout(self.former_section)
        self.former_portrait_layout.setSpacing(10)
        self.former_portrait_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.former_portrait_layout.setContentsMargins(0, 10, 0, 0)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(255, 255, 255, 40);")
        self.former_portrait_layout.addWidget(divider)

        self.former_section.setVisible(False)
        self._former_expanded = False

        # building column
        layout.addLayout(self.active_portrait_layout)
        layout.addSpacing(10)
        layout.addWidget(self.former_toggle_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.former_section)
        layout.addStretch()

        # building scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(140)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollBar:vertical {{width: 0px;}}")
        scroll.setWidget(column_inner)
        return scroll

    def _build_post_draft_feed(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        self.post_draft_feed_title = QLabel("")
        self.post_draft_feed_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(SCROLL_STYLESHEET)

        self._post_feed_container = QWidget()
        self._post_feed_layout = QVBoxLayout(self._post_feed_container)
        self._post_feed_layout.setContentsMargins(0, 4, 0, 4)
        self._post_feed_layout.setSpacing(0)
        self._post_feed_layout.addStretch()
        scroll.setWidget(self._post_feed_container)

        post_chat_row = QHBoxLayout()
        self.post_chat_input = QLineEdit()
        self.post_chat_input.setPlaceholderText("Send a message...")
        self.post_chat_input.setMaxLength(128)
        self.post_chat_input.returnPressed.connect(self._send_chat)
        self.post_chat_send_btn = QPushButton("Send")
        self.post_chat_send_btn.setFixedWidth(70)
        self.post_chat_send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.post_chat_send_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        self.post_chat_send_btn.clicked.connect(self._send_chat)
        post_chat_row.addWidget(self.post_chat_input)
        post_chat_row.addWidget(self.post_chat_send_btn)

        layout.addWidget(self.post_draft_feed_title)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(post_chat_row)

        return container

    def _build_stat_container(self):
        container = QWidget()
        self.stat_detail_layout = QVBoxLayout(container)
        self.stat_detail_layout.setContentsMargins(30, 20, 30, 20)
        self.stat_detail_layout.setSpacing(15)
        self.stat_detail_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # initial placeholder
        placeholder = QLabel("Select a player to view their stats.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 16px; color: #AAAAAA;")
        self.stat_detail_layout.addWidget(placeholder)

        return container

    def _build_portrait_button(self, player: dict, inactive: bool = False) -> QLabel:
        # grab name then image path
        name = player.get("id", "-")
        pixmap = Session.get_pixmap("players", name)

        # return consistent styled image
        image = QLabel()
        image.setFixedSize(100, 100)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        image.setStyleSheet("border: 2px solid #BBBBBB;")
        image.setCursor(Qt.CursorShape.PointingHandCursor)

        # grey out when inactive
        if inactive:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor("gray"))
            effect.setStrength(1.0)
            image.setGraphicsEffect(effect)
            image.setStyleSheet("border: 2px solid #555555;")

        # update stats when clicked; switch off feed if open
        def _on_click(e, p=player):
            self.right_panel.setCurrentIndex(0)
            self._update_stat_container(p)
        image.mousePressEvent = _on_click

        return image

    def _update_active_portraits(self):
        # clear existing
        while self.active_portrait_layout.count():
            item = self.active_portrait_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # iterate through standings
        players = self.my_team_standings.get("players", []) if self.my_team_standings else []
        for player in players:
            portrait = self._build_portrait_button(player, inactive=False)
            self.active_portrait_layout.addWidget(portrait, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _update_former_portraits(self):
        # clear existing
        while self.former_portrait_layout.count():
            item = self.former_portrait_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # iterate through former standings
        inactive_players = self.my_ex_players or []
        self.former_toggle_btn.setVisible(bool(inactive_players))
        for player in inactive_players:
            portrait = self._build_portrait_button(player, inactive=True)
            self.former_portrait_layout.addWidget(portrait, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _update_stat_container(self, player: dict):
        player_id = player.get("id", "-")

        # empty stat detail cont
        while self.stat_detail_layout.count():
            item = self.stat_detail_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # cache hit then return early
        if player_id in self._stat_cache:
            self.stat_detail_layout.addWidget(self._stat_cache[player_id])
            return

        # loading placeholder while async runs
        loading = QLabel("Loading...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        self.stat_detail_layout.addWidget(loading)

        joined = player.get("joined_at", "")
        left   = player.get("left_at")

        def _success(timeline):
            widget = self._build_stat_card(player, timeline)
            self._stat_cache[player_id] = widget

            while self.stat_detail_layout.count():
                item = self.stat_detail_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            self.stat_detail_layout.addWidget(widget)
            SoundManager.play("button")
        
        def _error(e):
            while self.stat_detail_layout.count():
                item = self.stat_detail_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            set_status(self, f"Failed to load history: {e}", code=2)

        # grabbing player score timeline async
        # manual delay: loads too fast but not fast enough - looks weird
        QTimer.singleShot(200, lambda: run_async(
            parent_widget=self.stat_container,
            fn=Session.event_service.get_player_points_timeline,
            args=(player_id, joined, left),
            block_cursor=False,
            on_success=_success,
            on_error=_error,
        ))

    def _build_stat_card(self, player: dict, timeline: list) -> QScrollArea:
        # for easy access
        name   = player.get("id", "-")
        region = player.get("region", "Unknown")
        points = player.get("points", 0)
        joined = player.get("joined_at", "")
        left   = player.get("left_at")

        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # top row with player and map
        top_widget = QWidget()
        top_widget.setFixedHeight(400)
        top_row = QHBoxLayout(top_widget)
        top_row.setSpacing(20)

        # left of top
        left_widget = QWidget()
        left_col = QVBoxLayout(left_widget)
        left_col.setSpacing(8)

        image = QLabel()
        image.setFixedSize(180, 180)
        image.setStyleSheet("border: 2px solid #FFFFFF;")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setPixmap(
            Session.get_pixmap("players", name).scaled(
                180, 180,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        region_img = ResourcePath.FLAGS / f"{region}.png"
        if not region_img.exists():
            region_img = ResourcePath.FLAGS / "placeholder.png"

        info_label = QLabel()
        info_label.setText(
            "<div style='line-height: 1.4;'>"
            f"<span style='font-size:20px; font-weight: bold;'>{name}</span><br/>"
            f"<span style='font-size:16px; color:#BBBBBB;'>{region}  </span>"
            f"<img src='{region_img}' width='18' height='12'><br/>"
            "</div>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        joined_str = joined.split("T")[0] if joined else "N/A"
        left_str   = left.split("T")[0] if left else "Present"
        tenure_label = QLabel(f"{joined_str}  till  {left_str}")
        tenure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tenure_label.setStyleSheet("font-size: 14px; color: #BBBBBB;")

        left_col.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(info_label)
        left_col.addWidget(tenure_label)

        # right of top
        svg_bytes = self._highlight_svg(region)
        map_widget = QSvgWidget()
        map_widget.load(svg_bytes)

        # maintain ratio
        svg_width = 600
        svg_height = int(svg_width * 857 / 2000)  # ≈ 120
        map_widget.setFixedSize(svg_width, svg_height)

        # adding to top row
        top_row.addWidget(left_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(map_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

        # stats row
        best_gained = max((e["points_gained"] for e in timeline), default=0)
        worst_gained = min((e["points_gained"] for e in timeline), default=0)
        avg_gained = round(points / len(timeline), 1) if timeline else 0

        stats_widget = QWidget()
        stats_widget.setStyleSheet("background-color: #090E2B; border-radius: 6px;")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(15, 12, 15, 12)
        stats_layout.setSpacing(0)

        for i, (label, value) in enumerate([
            ("Events Played", str(len(timeline))),
            ("Total Points",  str(points)),
            ("AVG. Pts/Event",str(avg_gained)),
            ("Best Event",    f"+{best_gained}"),
            ("Worst Event",   f"+{worst_gained}"),
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

        # divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(255,255,255,40);")

        layout.addWidget(top_widget)
        layout.addWidget(stats_widget)
        layout.addWidget(divider)

        # chart
        if not timeline:
            empty = QLabel("No event history available.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #AAAAAA; font-size: 16px;")
            layout.addWidget(empty)
        else:
            layout.addWidget(PointsChart(
                timeline,
                joined_at=joined,
            ))

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidget(frame)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        return scroll
  
    def _highlight_svg(self, region: str) -> bytes:
        '''
        helper svg magic method that highlights countries in the world map.
        searches country by name and adds a fill style tag
        '''
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
    

# -- BUTTON METHODS --

    def create_league(self):
        name = self.create_league_input.text().strip()
        self.create_league_input.setText("")
        if not name:
            set_status(self, "Please enter a league name.", code=2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "League created successfully!", code=1)

        def _error(error):
            set_status(self, f"Failed to create league: {error}", code=2)

        set_status(self, "Creating League...")
        run_async(parent_widget=self.history_area, fn=Session.league_service.create_then_join_league, args=(name,), on_success=_success, on_error=_error)

    def join_league(self):
        league_id = self.join_input.text().strip()
        self.join_input.setText("")
        if not league_id:
            set_status(self, "Please enter a league ID.", code=2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "League joined successfully!", code=1)

        def _error(error):
            set_status(self, f"Failed to join league: {error}", code=2)

        set_status(self, "Joining League...")
        run_async(parent_widget=self.history_area, fn=Session.league_service.join_league, args=(league_id,), on_success=_success, on_error=_error)

    def _toggle_post_draft_feed(self):
        current = self.right_panel.currentIndex()
        self.right_panel.setCurrentIndex(1 if current == 0 else 0)

    def _send_chat(self):
        # Accept input from either the pre-draft or post-draft chat box
        if self.is_draft_complete:
            message = self.post_chat_input.text().strip()
            self.post_chat_input.clear()
            btn = self.post_chat_send_btn
        else:
            message = self.chat_input.text().strip()
            self.chat_input.clear()
            btn = self.chat_send_btn

        if not message:
            return

        def _success(_):
            pass

        def _error(e):
            set_status(self, f"Failed to send message: {e}", code=2)

        run_async(
            parent_widget=btn,
            fn=Session.league_service.send_chat_message,
            args=(message, self.my_username,),
            block_cursor=False,
            on_success=_success,
            on_error=_error,
        )

    def leave_league(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Leave League")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Are you sure you would like to leave your league?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        ok_btn = msg.addButton("Leave", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("button")
        msg.exec()

        if msg.clickedButton() != ok_btn:
            set_status(self, "Leave cancelled.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "League left successfully!", code=1)

        def _error(error):
            set_status(self, f"Failed to leave league: {error}", code=2)

        set_status(self, "Leaving League...")
        run_async(parent_widget=self.history_area, fn=Session.league_service.leave_league, args=(), on_success=_success, on_error=_error)

    def assign_draft_order(self):
        usernames = self.draft_input.text().strip()
        if not usernames:
            set_status(self, "Please enter a list of usernames.", code=2)
            return
        user_list = [name.strip() for name in usernames.split(",")]

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "Draft order assigned successfully!", code=1)

        def _error(error):
            set_status(self, f"Failed to assign draft order: {error}", code=2)

        set_status(self, "Assigning draft order...")
        run_async(parent_widget=self.history_area, fn=Session.league_service.assign_draft_order, args=(user_list,), on_success=_success, on_error=_error)

    def begin_draft(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Begin Draft")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Beginning the draft will lock your league, preventing any member leaving or joining, and preventing the changing of the forfeit. Continue?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        ok_btn = msg.addButton("Begin draft", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("prompt")
        msg.exec()

        if msg.clickedButton() != ok_btn:
            set_status(self, "Draft cancelled.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "Draft started successfully!", code=1)

        def _error(error):
            set_status(self, f"Failed to begin draft: {error}", code=2)

        set_status(self, "Beginning draft...")
        run_async(parent_widget=self.history_area, fn=Session.league_service.begin_draft, args=(), on_success=_success, on_error=_error)

    def set_forfeit(self):
        forfeit = self.forfeit_input.text().strip()
        self.forfeit_input.setText("")
        if not forfeit:
            set_status(self, "Please enter a forfeit.", code=2)
            return

        def _success(success):
            if success:
                self.my_league_forfeit = forfeit
                fit_text_to_width(label=self.forfeit_label, text=self.my_league_forfeit, max_width=400, max_font_size=12)
                set_status(self, "Forfeit set!", code=1)

        def _error(error):
            set_status(self, f"Failed to set forfeit: {error}", code=2)

        run_async(parent_widget=self.history_area, fn=Session.league_service.set_forfeit, args=(forfeit,), on_success=_success, on_error=_error)

    def pick_player(self):
        selected = self.pick_list.currentItem()
        if not selected:
            set_status(self, "Please select a player from the list.", 2)
            return
        player = selected.text()
        self.pick_search.setText("")

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, f"Welcome {player} to {self.my_team_name}!", 1)

        def _error(error):
            set_status(self, f"Failed to pick player: {error}", 2)

        set_status(self, "Picking player...", 0)
        run_async(parent_widget=self.history_area, fn=Session.team_service.pick_player, args=(player,), on_success=_success, on_error=_error)

    def create_team(self):
        team_name = self.create_team_input.text().strip()
        self.create_team_input.setText("")
        if not team_name:
            set_status(self, "Please enter a team name.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "Team created successfully!", 1)

        def _error(error):
            set_status(self, f"Failed to create team: {error}", 2)

        set_status(self, "Creating team...", 0)
        run_async(parent_widget=self.history_area, fn=Session.team_service.create_team, args=(team_name,), on_success=_success, on_error=_error)

    def _toggle_settings(self):
        if self.history_stack.currentIndex() == self._HS_OWNER:
            self.history_stack.setCurrentIndex(self._HS_HISTORY)
            self.settings_toggle_btn.setText("Settings")
        else:
            self.history_stack.setCurrentIndex(self._HS_OWNER)
            self.settings_toggle_btn.setText("Close")
        SoundManager.play("button")

    def _toggle_picker(self):
        if self.history_stack.currentIndex() == self._HS_PICKER:
            self.history_stack.setCurrentIndex(self._HS_HISTORY)
            self.picker_toggle_btn.setText("Pick Player")
        else:
            self.history_stack.setCurrentIndex(self._HS_PICKER)
            self.picker_toggle_btn.setText("View Feed")
        SoundManager.play("button")

    def toggle_former_players(self):
        self._former_expanded = not self._former_expanded
        self.former_section.setVisible(self._former_expanded)
        self.former_toggle_btn.setText(
            "▲ Former" if self._former_expanded else "▼ Former"
        )
        SoundManager.play("button")

    def _view_help(self):
        SoundManager.play("button")

        dialog = QDialog(self)
        dialog.setWindowTitle("Info")
        dialog.setStyleSheet("background: #10194D;")
        dialog.setFixedSize(800,600)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20,10,20,10)

        title = QLabel("Leagues")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        title.setStyleSheet("font-weight: bold; font-size: 24px")

        with open(str(ResourcePath.TEXTS / "league_help.txt"), "r") as file:
            text_list = file.read().splitlines()

        def _create_label(text):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 14px")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            return label

        layout.addWidget(title)
        for idx, text in enumerate(text_list):
            if idx==2:
                tempC = QWidget()
                tempL = QHBoxLayout(tempC)

                tempL.addWidget(_create_label(text))
                img_label = QLabel()
                img_label.setPixmap(QPixmap(str(ResourcePath.IMAGES / "draft_example.png")).scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tempL.addWidget(img_label)

                layout.addWidget(tempC)
            else:
                layout.addWidget(_create_label(text))


        dialog.exec()


# -- REFRESHERS --

    def _refresh(self, force=0):
        draft_complete_before = getattr(self, "is_draft_complete", None)

        Session.init_player_scores()
        Session.init_league_data(force)

        league              = Session.league_data or {}
        team                = Session.team_data or {}

        self.my_league_history  = Session.league_history or []
        self.my_league_chat     = Session.league_chat or []
        self._seen_chat_ids     = {e["id"] for e in self.my_league_chat if e.get("id")}

        self.my_username        = Session.user
        self.my_user_id         = Session.user_id

        self.my_league_id       = league.get("league_id")
        self.my_league_name     = league.get("league_name")
        self.my_league_forfeit  = league.get("forfeit")
        self.is_league_locked   = league.get("locked", False)
        self.is_draft_complete  = league.get("draft_complete", False)
        self.is_owner           = league.get("league_owner") == self.my_user_id
        self.my_draft_order     = league.get("draft_order") or []
        self.my_next_pick       = league.get("next_pick")
        leaguemates             = league.get("leaguemates") or []
        self.my_leaguemates_raw = leaguemates
        self.my_leaguemates     = [d["manager_name"] for d in leaguemates]
        self.my_capacity        = f"{len(leaguemates)}/5"

        self.my_team_name       = team.get("team_name")
        self.my_team_standings  = team
        self.my_ex_players      = team.get("inactive_players") or []

        if draft_complete_before is not None and draft_complete_before != self.is_draft_complete:
            def _transition():
                self.app.stack.removeWidget(self.app.league_view)
                self.app.league_view.deleteLater()
                self.app.league_view = None
                self.app.show_league_view()
            QTimer.singleShot(0, _transition)
            return

        new_fingerprint = (
            self.my_league_name,
            self.is_draft_complete,
            self.is_league_locked,
            self.my_next_pick,
            self.my_team_name,
            tuple(self.my_leaguemates),
            tuple(p["id"] for p in (self.my_team_standings.get("players") or [])),
            len(self.my_league_history),
            len(self.my_league_chat),
        )

        self._sync_realtime_listener()

        if getattr(self, "_last_fingerprint", None) == new_fingerprint:
            return

        self._last_fingerprint = new_fingerprint
        self._update_view()

    def _on_realtime_ping(self, topic):
        if topic == "chat":
            try:
                new_chat = Session.league_service.get_league_chat() or []
            except Exception:
                return
            new_entries = [e for e in new_chat if e.get("id") not in self._seen_chat_ids]
            self._seen_chat_ids.update(e["id"] for e in new_entries if e.get("id"))
            self.my_league_chat = new_chat
            for entry in new_entries:
                self._prepend_chat_row(entry)
        else:
            self._refresh(force=1)

    def _prepend_chat_row(self, entry):
        from datetime import datetime, timezone
        sender  = entry.get("sender", "")
        msg     = entry.get("message", "")
        ts      = entry.get("created_at", "")

        try:
            dt     = datetime.fromisoformat(ts).astimezone(timezone.utc)
            ts_str = dt.strftime("%b %d, %H:%M")
        except Exception:
            ts_str = ts[:16] if ts else ""

        html = (
            f"<span style='color:#B39DDB;'>{sender}:</span>"
            f" <span style='color:#FFFFFF;'>{msg}</span>"
        )

        for layout in (self._history_feed_layout, self._post_feed_layout):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 10, 8, 10)
            row_layout.setSpacing(8)

            bullet = QLabel("•")
            bullet.setStyleSheet("font-size: 18px; color: #555555;")
            bullet.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

            msg_label = QLabel(f"<span style='font-size:18px; color:#888888;'>{html}</span>")
            msg_label.setTextFormat(Qt.TextFormat.RichText)
            msg_label.setWordWrap(True)
            msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            ts_label = QLabel(ts_str)
            ts_label.setStyleSheet("font-size: 12px; color: #555555;")
            ts_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ts_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

            row_layout.addWidget(bullet, alignment=Qt.AlignmentFlag.AlignTop)
            row_layout.addWidget(msg_label)
            row_layout.addWidget(ts_label, alignment=Qt.AlignmentFlag.AlignTop)

            layout.insertWidget(0, row)

    def _sync_realtime_listener(self):
        league_id = self.my_league_id
        should_listen = bool(league_id)

        if not should_listen:
            self._stop_realtime_listener()
            return

        # Already listening to the correct league — nothing to do
        if self._realtime_listener is not None and self._realtime_listener.isRunning():
            if getattr(self._realtime_listener, '_league_id', None) == league_id:
                return
            # League changed (shouldn't normally happen, but handle it)
            self._stop_realtime_listener()

        auth = Session.auth_base
        self._realtime_listener = RealtimeListener(
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            league_id=league_id,
        )
        self._realtime_listener.ping.connect(self._on_realtime_ping)
        self._realtime_listener.start()

    def _stop_realtime_listener(self):
        if self._realtime_listener is not None:
            self._realtime_listener.ping.disconnect()
            self._realtime_listener.stop()
            self._realtime_listener = None

    def _update_view(self):
        if self.my_league_id:
            if self.is_draft_complete:
                self._show_post_draft_state()
            else:
                self._show_pre_draft_state()
        else:
            self._show_no_league_state()

    def _show_no_league_state(self):
        self.view_stack.setCurrentWidget(self.no_league_page)

    def _show_pre_draft_state(self):
        self.view_stack.setCurrentWidget(self.pre_draft_page)

        has_team = bool(self.my_team_name)

        # Header
        fit_text_to_width(label=self.league_name_label, text=self.my_league_name or "", max_width=400)
        self.league_id_label.setText(str(self.my_league_id or ""))
        self.capacity_label.setText(f"Members: {self.my_capacity}")
        self.members_list_label.setText(", ".join(self.my_leaguemates))
        self._update_history_feed()

        # Sidebar draft order
        if self.my_draft_order:
            self.draft_order_label.setText(", ".join(self.my_draft_order))
        else:
            self.draft_order_label.setText("Not set")

        # Sidebar forfeit
        if self.my_league_forfeit:
            self.forfeit_label.setText(self.my_league_forfeit)
        else:
            self.forfeit_label.setText("Not yet set.")

        # Roster bar
        self.team_overview.setVisible(has_team)
        self._roster_divider_wrapper.setVisible(has_team)
        if has_team:
            self.team_name_label.setText(self.my_team_name or "")
            self._update_player_slots()

        # Leave button
        self.leave_btn.setVisible(not self.is_league_locked and not self.is_draft_complete)

        # Next pick avatar (draft phase only)
        if self.is_league_locked:
            self._refresh_next_pick_avatar()
            self.next_pick_label.setText(f"Next: {self.my_next_pick or '?'}")
        self.next_pick_avatar_slot.setVisible(self.is_league_locked)
        self.next_pick_label.setVisible(self.is_league_locked)

        # Owner settings toggle only shown pre-lock; never during draft
        self.settings_toggle_btn.setVisible(self.is_owner and not self.is_league_locked)
        # Reset settings panel if hidden (e.g. draft just started while settings were open)
        if not self.settings_toggle_btn.isVisible():
            self.settings_toggle_btn.setText("Settings")
            if self.history_stack.currentIndex() == self._HS_OWNER:
                self.history_stack.setCurrentIndex(self._HS_HISTORY)

        # history_stack page selection — state always wins over manual toggle
        is_my_pick = (
            self.is_league_locked
            and not self.is_draft_complete
            and self.my_username == self.my_next_pick
        )

        if is_my_pick and not has_team:
            self.history_stack.setCurrentIndex(self._HS_CREATOR)
            self.picker_toggle_btn.setVisible(False)
        elif is_my_pick and has_team:
            self.history_stack.setCurrentIndex(self._HS_PICKER)
            self._refresh_pick_input()
            self._update_pick_preview()
            # Picker toggle: lets user glance at history and come back
            self.picker_toggle_btn.setText("View History")
            self.picker_toggle_btn.setVisible(True)
            # Sound: only play once per turn (guard against double-pick consecutive rounds)
            if self._last_pick_turn_notified != self.my_next_pick:
                self._last_pick_turn_notified = self.my_next_pick
                SoundManager.play("prompt")
        elif self.is_league_locked and has_team:
            # Draft is running but it's not this user's turn — force back to history
            if self.history_stack.currentIndex() == self._HS_PICKER:
                self.history_stack.setCurrentIndex(self._HS_HISTORY)
            self.picker_toggle_btn.setVisible(False)
        else:
            self.picker_toggle_btn.setVisible(False)
            # Only reset to history if not currently in the owner panel
            if self.history_stack.currentIndex() not in (self._HS_OWNER,):
                self.history_stack.setCurrentIndex(self._HS_HISTORY)

    def _show_post_draft_state(self):
        self.view_stack.setCurrentWidget(self.post_draft_page)

        # Update header strip
        self.strip_league_name.setText(self.my_league_name or "")
        members_text = ", ".join(self.my_leaguemates)
        self.strip_members_label.setText(members_text)
        self.strip_forfeit_label.setText(f"Forfeit: {self.my_league_forfeit}" or "")
        self.post_draft_feed_title.setText(self.my_league_name or "")
        self._update_post_draft_feed()

        # Update portraits
        self._update_active_portraits()
        self._update_former_portraits()

    def _update_post_draft_feed(self):
        from datetime import datetime, timezone

        while self._post_feed_layout.count() > 1:
            item = self._post_feed_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for ts, html in self._merge_feed_events():
            try:
                ts_str = datetime.fromisoformat(ts).astimezone(timezone.utc).strftime("%b %d, %H:%M")
            except Exception:
                ts_str = ts[:16] if ts else ""
            self._post_feed_layout.insertWidget(
                self._post_feed_layout.count() - 1,
                self._build_feed_row(html, ts_str)
            )

    def _update_player_slots(self):
        players = self.my_team_standings.get("players", []) if self.my_team_standings else []

        for i in reversed(range(self.team_bar_layout.count())):
            widget = self.team_bar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
            else:
                slot = self._build_player_slot({})
            self.team_bar_layout.addWidget(slot, stretch=1)

   
# -- HELPERS --

    def _refresh_next_pick_avatar(self):
        while self.next_pick_avatar_slot_layout.count():
            item = self.next_pick_avatar_slot_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        user_id = self._get_user_id_for_username(self.my_next_pick)
        if not user_id:
            return

        avatar_bytes = Session.init_avatar(user_id)
        if not avatar_bytes:
            return

        pixmap = QPixmap()
        pixmap.loadFromData(avatar_bytes)
        if not pixmap.isNull():
            avatar = HoverImage(pixmap, size=86, border_width=2, border_color="#88ff87")
            self.next_pick_avatar_slot_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

    def _get_user_id_for_username(self, username: str):
        for m in (self.my_leaguemates_raw or []):
            if m.get("manager_name") == username:
                return str(m.get("user_id", ""))
        return None

    def _on_pick_search_changed(self, text: str):
        if not text:
            self._populate_pick_list(self._all_pick_names)
        else:
            filtered = [n for n in self._all_pick_names if text.lower() in n.lower()]
            self._populate_pick_list(filtered)

    def _on_pick_list_select(self, item):
        self._pending_pick_name = item.text()
        self._pick_preview_timer.start()

    def _do_pick_preview_update(self):
        name = getattr(self, "_pending_pick_name", "")
        if not name:
            self.pick_preview_image.update_pixmap(self._pick_preview_pixmap)
            return
        if name not in self._pick_pixmap_cache:
            self._pick_pixmap_cache[name] = Session.get_pixmap("players", name)
        self.pick_preview_image.update_pixmap(self._pick_pixmap_cache[name])

    def _update_pick_preview(self):
        pass

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh(force=0)

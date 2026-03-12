import re
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFontMetrics, QPixmap, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QGridLayout,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QGroupBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QStackedWidget,
    QScrollArea,
    QGraphicsColorizeEffect
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async
from app.client.widgets.painter import PointsChart
from app.client.theme import *


REGION_SVG_MAP = {
    "Australia":          ("class", "Australia"),
    "Belgium":            ("id",    "BE"),
    "Brazil":             ("id",    "BR"),
    "Cameroon":           ("id",    "CM"),
    "Canada":             ("class", "Canada"),
    "Chile":              ("class", "Chile"),
    "China":              ("class", "China"),
    "Dominican Republic": ("id",    "DO"),
    "France":             ("class", "France"),
    "Hong Kong":          ("class", "China"),       # proxy: China
    "Japan":              ("class", "Japan"),
    "Norway":             ("class", "Norway"),
    "Saudi Arabia":       ("id",    "SA"),
    "Singapore":          ("id",    "MY"),           # proxy: Malaysia
    "South Korea":        ("id",    "KR"),
    "Sweden":             ("id",    "SE"),
    "Taiwan":             ("id",    "TW"),
    "UAE":                ("id",    "AE"),
    "United Kingdom":     ("class", "United Kingdom"),
    "United States":      ("class", "United States"),
}

class LeagueView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.connect_refresh(lambda: self._refresh(force=1))

        self._stat_cache = {}

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
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        page_layout.addSpacerItem(QSpacerItem(20, 30))

        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # League side
        self.league_widget = QWidget()
        self.league_widget.setFixedWidth(600)
        self.league_layout = QVBoxLayout(self.league_widget)
        self.league_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.league_layout.setContentsMargins(20, 0, 20, 0)
        self.league_layout.setSpacing(20)

        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.divider.setLineWidth(2)
        self.divider.setStyleSheet("color: #444444;")
        self.divider.setFixedWidth(2)

        # Team side
        self.team_widget = QWidget()
        self.team_widget.setFixedWidth(600)
        self.team_layout = QVBoxLayout(self.team_widget)
        self.team_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.team_layout.setContentsMargins(20, 0, 20, 20)
        self.team_layout.setSpacing(20)

        main_layout.addWidget(self.league_widget, stretch=1)
        main_layout.addWidget(self.divider)
        main_layout.addWidget(self.team_widget, stretch=1)

        page_layout.addWidget(main, stretch=1)

        # League column
        self.in_league_display    = self._build_in_league_display()
        self.owner_controls       = self._build_owner_controls()
        self.leave                = self._build_leave_button()

        self.league_layout.addWidget(self.in_league_display)
        self.league_layout.addStretch()
        self.league_layout.addWidget(self.owner_controls)
        self.league_layout.addStretch()
        self.league_layout.addWidget(self.leave)

        # Team column
        self.team_creator   = self._build_team_creator()
        self.team_info      = self._build_team_info()
        self.draft_picker   = self._build_draft_picker()
        self.team_overview  = self._build_roster_overview()
        self.player_stats   = self._build_player_stat_section()

        self.team_layout.addWidget(self.team_info)
        self.team_layout.addWidget(self.team_overview)
        self.team_layout.addWidget(self.draft_picker)
        self.team_layout.addWidget(self.player_stats)
        self.team_layout.addWidget(self.team_creator)

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

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("color: #444444;")
        vline.setFixedWidth(2)

        team_area_layout.addWidget(self.active_player_column)
        team_area_layout.addWidget(vline)
        team_area_layout.addWidget(self.stat_container, stretch=1)

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
        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_league_input)
        create_group.setLayout(create_group_layout)

        create_btn = QPushButton("Create")
        create_btn.setFixedWidth(100)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.clicked.connect(self.create_league)

        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")
        self.join_input.returnPressed.connect(self.join_league)

        join_group = QGroupBox("Join League")
        join_group.setStyleSheet("QGroupBox { color: white; }")
        join_group_layout = QVBoxLayout()
        join_group_layout.addWidget(self.join_input)
        join_group.setLayout(join_group_layout)

        join_btn = QPushButton("Join")
        join_btn.setFixedWidth(100)
        join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        join_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        join_btn.clicked.connect(self.join_league)

        create_row = QHBoxLayout()
        create_row.addWidget(create_group)
        create_row.addWidget(create_btn)
        create_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        join_row = QHBoxLayout()
        join_row.addWidget(join_group)
        join_row.addWidget(join_btn)
        join_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setSpacing(25)
        layout.addLayout(join_row)
        layout.addLayout(create_row)
        return cont


# -- PRE DRAFT BUILDERS

    def _build_owner_controls(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Alice, Bob, Charlie")
        self.draft_input.returnPressed.connect(self.assign_draft_order)

        group = QGroupBox("Assign Draft Order")
        group.setStyleSheet("QGroupBox { color: white; }")
        group_layout = QHBoxLayout()
        group_layout.addWidget(self.draft_input)
        group.setLayout(group_layout)

        set_btn = QPushButton("Set Order")
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        set_btn.clicked.connect(self.assign_draft_order)

        begin_btn = QPushButton("Begin Draft")
        begin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        begin_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        begin_btn.clicked.connect(self.begin_draft)

        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Loser must...")
        self.forfeit_input.returnPressed.connect(self.set_forfeit)

        forfeit_group = QGroupBox("Set Forfeit")
        forfeit_group.setStyleSheet("QGroupBox { color: white; }")
        forfeit_group_layout = QVBoxLayout()
        forfeit_group_layout.addWidget(self.forfeit_input)
        forfeit_group.setLayout(forfeit_group_layout)

        forfeit_btn = QPushButton("Submit")
        forfeit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forfeit_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        forfeit_btn.clicked.connect(self.set_forfeit)

        cont = QWidget()
        cont_layout = QVBoxLayout(cont)

        row = QHBoxLayout()
        row.addWidget(group)
        row.addWidget(set_btn)
        row.addWidget(begin_btn)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        forfeit_row = QHBoxLayout()
        forfeit_row.addWidget(forfeit_group)
        forfeit_row.addWidget(forfeit_btn)
        forfeit_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cont_layout.addLayout(row)
        cont_layout.addLayout(forfeit_row)

        cont.setVisible(False)

        self.draft_controls  = cont
        layout.addWidget(cont)
        
        return container

    def _build_in_league_display(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.league_info           = self._build_league_info()
        self.draft_info_container  = self._build_draft_info()

        layout.addWidget(self.league_info)
        layout.addWidget(self.draft_info_container)

        container.setVisible(False)
        return container

    def _build_leave_button(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        self.leave_btn = QPushButton("Leave League")
        self.leave_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.leave_btn.setStyleSheet(BUTTON_STYLESHEET_D)
        self.leave_btn.clicked.connect(self.leave_league)
        layout.addWidget(self.leave_btn)

        return container

    def _build_league_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self.league_name_label = QLabel("")
        self.league_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_name_label.setStyleSheet("font-weight: bold;")

        self.league_owner = QLabel("")
        self.league_owner.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.league_owner.setStyleSheet(BUTTON_STYLESHEET_D)

        layout.addWidget(self.league_name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.league_owner, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacerItem(QSpacerItem(20, 25))

        self.league_id_label = QLabel("")
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.league_id_label.setStyleSheet("QLabel { color: white; font-size: 14px; }")

        self.forfeit_label = QLabel("")
        self.forfeit_label.setStyleSheet("font-weight:bold; color:#ff8168;")

        self.leaguemates = QLabel("")
        self.leaguemates.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.leaguemates.setStyleSheet("QLabel { color: white; font-size: 16px; }")
        self.leaguemates.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.leaguemates.setFixedWidth(400)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(1, 400)

        grid.addWidget(QLabel("League ID:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.league_id_label,  0, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Members:"),    1, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.leaguemates,      1, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Forfeit:"),    2, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.forfeit_label,    2, 1, Qt.AlignmentFlag.AlignRight)

        layout.addLayout(grid)
        return container

    def _build_draft_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self.draft_order_label = QLabel("N/A")
        self.draft_order_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.draft_order_label.setFixedWidth(400)

        self.next_pick_label = QLabel("N/A")
        self.next_pick_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.next_pick_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #88ff87;")

        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        grid.addWidget(QLabel("Draft Order:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.draft_order_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Next Pick:"),   1, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.next_pick_label,   1, 1, Qt.AlignmentFlag.AlignRight)

        layout.addLayout(grid)
        container.setVisible(False)
        return container

    def _build_team_creator(self):
        self.team_creator_container = QWidget()
        layout = QVBoxLayout(self.team_creator_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.create_team_input = QLineEdit()
        self.create_team_input.setPlaceholderText("My Team...")
        self.create_team_input.returnPressed.connect(self.create_team)

        create_group = QGroupBox("Create your Team!")
        create_group.setStyleSheet("QGroupBox { color: white; }")
        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_team_input)
        create_group.setLayout(create_group_layout)

        create_label = QLabel("Create a team here!")
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        create_btn = QPushButton("Create")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.clicked.connect(self.create_team)

        create_layout = QHBoxLayout()
        create_layout.addWidget(create_group, stretch=1)
        create_layout.addWidget(create_btn)
        create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(create_label)
        layout.addSpacing(10)
        layout.addLayout(create_layout)
        return self.team_creator_container

    def _build_team_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.team_name_label = QLabel("")
        self.team_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.team_name_label)
        return container

    def _build_draft_picker(self):
        self.pick_container = QWidget()
        layout = QVBoxLayout(self.pick_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.pick_input = QComboBox()
        player_names = sorted([p["name"] for p in Session.player_scores], key=str.casefold)
        self.pick_input.addItems(player_names)
        self.pick_input.setEditable(True)
        self.pick_input.setStyleSheet("""
                                        QComboBox QAbstractItemView { 
                                        color: white; 
                                        }
                                        QComboBox::drop-down {
                                            width: 20px;
                                        }
                                    """)
        self.pick_input.setPlaceholderText("Blaz, MenaRD, Leshar...")
        self.pick_input.lineEdit().returnPressed.connect(self.pick_player)

        group = QGroupBox("Pick a Player!")
        group.setStyleSheet("QGroupBox { color: white; }")
        group_layout = QVBoxLayout()
        group_layout.addWidget(self.pick_input)
        group.setLayout(group_layout)

        label = QLabel("It's your turn to pick a player!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        btn = QPushButton("Pick")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BUTTON_STYLESHEET_A)
        btn.clicked.connect(self.pick_player)

        pick_layout = QHBoxLayout()
        pick_layout.addWidget(group, stretch=1)
        pick_layout.addWidget(btn, stretch=1)
        pick_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addSpacing(10)
        layout.addLayout(pick_layout)
        return self.pick_container

    def _build_roster_overview(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self.team_bar_layout = QHBoxLayout()
        self.team_bar_layout.setSpacing(10)
        self.team_bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(self.team_bar_layout)
        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(5)

        image = QLabel()
        image.setFixedSize(QSize(75, 75))
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        if player:
            player_name = player.get("id", "-")
            image.setPixmap(
                Session.get_pixmap("players", player_name).scaled(
                    75, 75,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            image.setStyleSheet("border: 2px solid #BBBBBB;")
            image.setCursor(Qt.CursorShape.PointingHandCursor)
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

        layout.addWidget(self.strip_league_name)
        layout.addWidget(self.strip_members_label)
        layout.addStretch()
        layout.addWidget(self.strip_forfeit_label)

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

        # update stats when clicked
        image.mousePressEvent = lambda e, p=player: self._update_stat_container(p)

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

        def _error(e):
            while self.stat_detail_layout.count():
                item = self.stat_detail_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            self._set_status(f"Failed to load history: {e}", code=2)

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
            self._set_status("Please enter a league name.", code=2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("League created successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to create league: {error}", code=2)

        self._set_status("Creating League...")
        run_async(parent_widget=self.league_widget, fn=Session.league_service.create_then_join_league, args=(name,), on_success=_success, on_error=_error)

    def join_league(self):
        league_id = self.join_input.text().strip()
        self.join_input.setText("")
        if not league_id:
            self._set_status("Please enter a league ID.", code=2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("League joined successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to join league: {error}", code=2)

        self._set_status("Joining League...")
        run_async(parent_widget=self.league_widget, fn=Session.league_service.join_league, args=(league_id,), on_success=_success, on_error=_error)

    def leave_league(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Leave League")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Are you sure you would like to leave your league?")
        msg.setIcon(QMessageBox.Icon.Warning)
        ok_btn = msg.addButton("Leave", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() != ok_btn:
            self._set_status("Leave cancelled.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("League left successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to leave league: {error}", code=2)

        self._set_status("Leaving League...")
        run_async(parent_widget=self.league_widget, fn=Session.league_service.leave_league, args=(), on_success=_success, on_error=_error)

    def assign_draft_order(self):
        usernames = self.draft_input.text().strip()
        if not usernames:
            self._set_status("Please enter a list of usernames.", code=2)
            return
        user_list = [name.strip() for name in usernames.split(",")]

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("Draft order assigned successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to assign draft order: {error}", code=2)

        self._set_status("Assigning draft order...")
        run_async(parent_widget=self.league_widget, fn=Session.league_service.assign_draft_order, args=(user_list,), on_success=_success, on_error=_error)

    def begin_draft(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Begin Draft")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Beginning the draft will lock your league, preventing any member leaving or joining, and preventing the changing of the forfeit. Continue?")
        msg.setIcon(QMessageBox.Icon.Question)
        ok_btn = msg.addButton("Begin draft", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() != ok_btn:
            self._set_status("Draft cancelled.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("Draft started successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to begin draft: {error}", code=2)

        self._set_status("Beginning draft...")
        run_async(parent_widget=self.league_widget, fn=Session.league_service.begin_draft, args=(), on_success=_success, on_error=_error)

    def set_forfeit(self):
        forfeit = self.forfeit_input.text().strip()
        self.forfeit_input.setText("")
        if not forfeit:
            self._set_status("Please enter a forfeit.", code=2)
            return

        def _success(success):
            if success:
                self.my_league_forfeit = forfeit
                Session.league_forfeit = forfeit
                self._fit_text_to_width(label=self.forfeit_label, text=self.my_league_forfeit, max_width=400, max_font_size=12)
                self._set_status("Forfeit set!", code=1)

        def _error(error):
            self._set_status(f"Failed to set forfeit: {error}", code=2)

        run_async(parent_widget=self.league_widget, fn=Session.league_service.set_forfeit, args=(forfeit,), on_success=_success, on_error=_error)

    def pick_player(self):
        player = self.pick_input.currentText()
        self.pick_input.setCurrentIndex(-1)
        if not player:
            self._set_status("Please enter a player name.", 2)
            return
        if not any(p["name"] == player for p in Session.player_scores):
            self._set_status(f"{player} not found. Names are case sensitive!", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status(f"Welcome {player} to {self.my_team_name}!", 1)

        def _error(error):
            self._set_status(f"Failed to pick player: {error}", 2)

        self._set_status("Picking player...", 0)
        run_async(parent_widget=self.team_widget, fn=Session.team_service.pick_player, args=(player,), on_success=_success, on_error=_error)

    def create_team(self):
        team_name = self.create_team_input.text().strip()
        self.create_team_input.setText("")
        if not team_name:
            self._set_status("Please enter a team name.", 2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("Team created successfully!", 1)

        def _error(error):
            self._set_status(f"Failed to create team: {error}", 2)

        self._set_status("Creating team...", 0)
        run_async(parent_widget=self.team_widget, fn=Session.team_service.create_team, args=(team_name,), on_success=_success, on_error=_error)

    def toggle_former_players(self):
        self._former_expanded = not self._former_expanded
        self.former_section.setVisible(self._former_expanded)
        self.former_toggle_btn.setText(
            "▲ Former" if self._former_expanded else "▼ Former"
        )


# -- REFRESHERS --

    def _refresh(self, force=0):
        Session.init_league_data(force)
        Session.init_player_scores()

        league              = Session.league_data or {}
        team                = Session.team_data or {}

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
        self.my_leaguemates     = [d["manager_name"] for d in leaguemates]
        self.my_capacity        = f"{len(leaguemates)}/5"

        self.my_team_name       = team.get("team_name")
        self.my_team_standings  = team
        self.my_ex_players      = team.get("inactive_players") or []

        self._update_view()

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

        # League column visibility
        self.in_league_display.setVisible(self.my_league_id is not None)
        self.owner_controls.setVisible(bool(self.is_owner))
        self.draft_controls.setVisible(not self.is_league_locked)
        self.divider.setVisible(self.my_league_id is not None)
        self.team_widget.setVisible(self.my_league_id is not None)

        leave_visible = (
            self.my_league_id is not None
            and not self.is_league_locked
            and not self.is_draft_complete
        )
        self.leave.setVisible(leave_visible)

        if self.my_league_id:
            self.league_owner.setVisible(self.is_owner)
            if self.is_owner:
                self.league_owner.setText("Owner")

            self.league_id_label.setText(str(self.my_league_id))
            self._fit_text_to_width(label=self.league_name_label, text=self.my_league_name, max_width=400)
            self._fit_text_to_width(label=self.leaguemates, text=", ".join(self.my_leaguemates), max_width=400, max_font_size=14, bold=False)

            if self.my_league_forfeit:
                self._fit_text_to_width(label=self.forfeit_label, text=self.my_league_forfeit, max_width=400, max_font_size=12)
            else:
                self.forfeit_label.setText("Forfeit not yet set.")

            self.draft_info_container.setVisible(True)
            if self.my_draft_order:
                self._fit_text_to_width(label=self.draft_order_label, text=", ".join(self.my_draft_order), max_width=400, max_font_size=14, bold=False)
            if self.is_league_locked:
                self.next_pick_label.setText(str(self.my_next_pick))
            if self.is_draft_complete:
                self.draft_info_container.setVisible(False)

        # Team column
        has_team = bool(self.my_team_name)
        self.team_creator.setVisible(not has_team)
        self.team_info.setVisible(has_team)
        self.team_overview.setVisible(has_team)
        self.draft_picker.setVisible(
            has_team
            and not self.is_draft_complete
            and self.my_username == self.my_next_pick
            and self.is_league_locked
        )

        self._update_player_stat(None)

        if has_team:
            self._fit_text_to_width(label=self.team_name_label, text=self.my_team_name, max_width=400)
            self._update_player_slots()

    def _show_post_draft_state(self):
        self.view_stack.setCurrentWidget(self.post_draft_page)

        # Update header strip
        self.strip_league_name.setText(self.my_league_name or "")
        members_text = ", ".join(self.my_leaguemates)
        self.strip_members_label.setText(members_text)
        self.strip_forfeit_label.setText(f"Forfeit: {self.my_league_forfeit}" or "")

        # Update portraits
        self._update_active_portraits()
        self._update_former_portraits()

    def _update_player_slots(self):
        players = self.my_team_standings.get("players", []) if self.my_team_standings else []

        for i in reversed(range(self.team_bar_layout.count())):
            widget = self.team_bar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.player_buttons = []
        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
                slot.mousePressEvent = lambda e, p=players[i]: self._update_player_stat(p)
                self.player_buttons.append(slot)
            else:
                slot = self._build_player_slot({})
            self.team_bar_layout.addWidget(slot, stretch=1)

    def _update_player_stat(self, player: dict | None):
        while self.player_detail_layout.count():
            item = self.player_detail_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if self.draft_picker.isVisible() or not player:
            return

        name      = player["id"]
        region    = player.get("region", "Unknown")
        points    = player["points"]
        joined_at = player["joined_at"]

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        image = QLabel()
        image.setStyleSheet("border: 2px solid #FFFFFF;")
        image.setFixedSize(200, 200)
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        image.setPixmap(
            Session.get_pixmap("players", name).scaled(
                200, 200,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        region_img = ResourcePath.FLAGS / f"{region}.png"
        if not region_img.exists():
            region_img = ResourcePath.FLAGS / "placeholder.png"

        info_label = QLabel()
        info_label.setText(
            "<div style='line-height: 1;'>"
            f"<span style='font-size:20px; font-weight: bold;'>{name}</span><br/>"
            f"<span style='font-size:16px; color:#BBBBBB;'>{region}  </span>"
            f"<img src='{region_img}' width='18' height='12'><br/>"
            "</div>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        points_label = QLabel(f"Points: {points}")
        points_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        joined_label = QLabel(f"Joined At: {joined_at.split('T')[0]}")
        joined_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(points_label)
        layout.addWidget(joined_label)

        self.player_detail_layout.addWidget(frame)

   
# -- HELPERS --

    def _set_status(self, msg, code=0):
        colors = {0: "#FFFFFF", 1: "#00ff0d", 2: "#FFD700"}
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {colors.get(code, '#FFFFFF')};
            }}
        """)
        self.status_label.setText(msg)

        if hasattr(self, "_status_timer") and self._status_timer.isActive():
            self._status_timer.stop()

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status_label.setText(""))
        self._status_timer.start(8000)

    def _fit_text_to_width(self, label: QLabel, text: str, max_width: int,
                           min_font_size=2, max_font_size=40, bold=True):
        if not text or max_width <= 0:
            return
        font = label.font()
        font.setBold(bold)
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

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh(force=0)

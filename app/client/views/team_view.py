from pathlib import Path

from datetime import datetime

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

from PyQt6.QtCore import Qt

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
        self.footer = FooterNav(self.app)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

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


# -- BUILDERS --

    def _build_team_creator(self):
        self.team_creator_container = QWidget()

        layout = QVBoxLayout(self.team_creator_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.create_input = QLineEdit()
        self.create_input.setPlaceholderText("My Team...")

        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_input)

        create_group = QGroupBox("Create your Team!")
        create_group.setLayout(create_group_layout)

        create_label = QLabel("Create a team here!")
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333; 
        """)

        create_btn = QPushButton("Pick")
        create_btn.setFixedWidth(100)
        create_btn.setFixedHeight(30)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ff9d00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ffaa22;
            }
            QPushButton:pressed {
                background-color: #de8900;
            }
        """)
        create_btn.clicked.connect(self.create_team)

        create_layout = QHBoxLayout()
        create_layout.addWidget(create_group, stretch=1)
        create_layout.addWidget(create_btn, stretch=1)
        create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(create_label)
        layout.addSpacing(10)
        layout.addLayout(create_layout)
        layout.addWidget(self._create_separator())
        
        return self.team_creator_container

    def _build_team_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.team_name_label = QLabel("")
        self.team_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.team_name_label.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold; 
            color: #333; 
        """)

        layout.addWidget(self.team_name_label)
        layout.addWidget(self._create_separator())

        return container

    def _build_draft_picker(self):
        self.pick_container = QWidget()

        layout = QVBoxLayout(self.pick_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.pick_input = QComboBox()
        player_names = [p["name"] for p in Session.player_scores]
        player_names_sorted = sorted(player_names, key=str.casefold)
        self.pick_input.addItems(player_names_sorted)
        self.pick_input.setEditable(True)
        self.pick_input.setPlaceholderText("Blaz, MenaRD, Leshar...")

        grou_layout = QVBoxLayout()
        grou_layout.addWidget(self.pick_input)

        group = QGroupBox("Pick a Player!")
        group.setLayout(grou_layout)

        label = QLabel("It's your turn to pick a player!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333; 
        """)

        btn = QPushButton("Pick")
        btn.setFixedWidth(100)
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ff9d00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ffaa22;
            }
            QPushButton:pressed {
                background-color: #de8900;
            }
        """)
        btn.clicked.connect(self.pick_player)

        pick_layout = QHBoxLayout()
        pick_layout.addWidget(group, stretch=1)
        pick_layout.addWidget(btn, stretch=1)
        pick_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addSpacing(10)
        layout.addLayout(pick_layout)
        layout.addWidget(self._create_separator())
        
        return self.pick_container

    def _build_roster_overview(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # player row
        self.team_bar_layout = QHBoxLayout()
        self.team_bar_layout.setSpacing(10)
        self.team_bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(self.team_bar_layout)
        layout.addWidget(self._create_separator())

        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        image = QLabel()
        image.setStyleSheet("border: 2px solid #333;")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setCursor(Qt.CursorShape.PointingHandCursor)

        PLAYER_IMG_DIR = Path("app/client/assets/player_pictures")

        player_name = player["id"]
        img_path = PLAYER_IMG_DIR / f"{player_name}.jpg"

        pixmap = QPixmap(str(img_path))
        if pixmap.isNull():
            pixmap = QPixmap(str(PLAYER_IMG_DIR / "placeholder.png"))

        image.setPixmap(
            pixmap.scaled(
                140, 140,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        name = QLabel(player["id"])
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #333; 
        """)

        layout.addWidget(image)
        layout.addWidget(name)

        return slot

    def _build_empty_player_slot(self):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        image = QLabel()
        image.setFixedSize(140, 140)
        image.setStyleSheet("""
            border: 2px dashed #aaa;
            background: #f0f0f0;
            color: #999;
        """)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setText("?")

        name = QLabel("-")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #999; 
        """)


        layout.addWidget(image)
        layout.addWidget(name)

        return slot

    def _build_player_stat_section(self):
        container = QWidget()
        self.player_detail_layout = QVBoxLayout(container)
        self.player_detail_layout.setContentsMargins(50, 0, 50, 0)
        self.player_detail_layout.setSpacing(15)

        return container

    def _update_player_stat(self, player: dict):
        # Clear previous stats
        while self.player_detail_layout.count():
            item = self.player_detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        PLAYER_IMG_DIR = Path("app/client/assets/player_pictures")
        REGION_ICO_DIR = Path("app/client/assets/icons/flags")

        name = player["id"]
        region = player.get("region", "Unknown")
        points = player["points"]
        joined_at = player["joined_at"]
        left_at = player["left_at"]
        active = left_at is None

        # Row container
        row = QFrame()
        row.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Player image
        image = QLabel()
        img_path = PLAYER_IMG_DIR / f"{name}.jpg"
        if not img_path.exists():
            img_path = PLAYER_IMG_DIR / "placeholder.png"
        pixmap = QPixmap(str(img_path)).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image.setPixmap(pixmap)
        layout.addWidget(image)

        # Info column
        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 25, 0, 25)

        region_img = REGION_ICO_DIR / f"{region}.png"
        if not region_img.exists():
            region_img = REGION_ICO_DIR / "placeholder.png"

        info_label = QLabel(f"<b>{name}</b><br>{region} <img src='{region_img}' width='18' height='12'>")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        info_col.addWidget(info_label)

        points_label = QLabel(f"Points: {points}")
        points_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        info_col.addWidget(points_label)

        joined_label = QLabel(f"Joined At: {joined_at.split('T')[0]}")
        joined_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        info_col.addWidget(joined_label)

        if not active:
            left_label = QLabel(f"Left At: {left_at.split('T')[0]}")
            left_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            info_col.addWidget(QLabel("Transferred"))
            info_col.addWidget(left_label)

        layout.addLayout(info_col)
        self.player_detail_layout.addWidget(row)


# -- BUTTON METHODS --

    def pick_player(self):
        player = self.pick_input.currentText()
        print("pick_player: CLICK")

        if not player:
            self._set_status("Please enter a player name.", 2)
            return
        
        if not any(p["name"] == player for p in Session.player_scores):
            self._set_status(f"{player} not found. Names are case sensitive!", 2)
            return
        
        def _success(success):
            if success:
                self._refresh()
                self._set_status(f"Welcome {player} to {self.my_team_name}!", 1)
        
        def _error(error):
            self._set_status(f"Failed to pick player: {error}", 2)
        
        self._set_status("Picking player...", 0)
        run_async(
            parent_widget= self.content_widget,
            fn= Session.team_service.pick_player,
            args= (player,),
            on_success=_success,
            on_error=_error
        )

    def create_team(self):
        team_name = self.create_input.text().strip()
        print("create_team: CLICK")

        if not team_name:
            self._set_status("Please enter a team name.", 2)
        
        def _success(success):
            if success:
                self._refresh()
                self._set_status("Team created successfuly!", 1)
        
        def _error(error):
            self._set_status(f"Failed to create team: {error}", 2)
        
        self._set_status("Creating team...", 0)
        run_async(
            parent_widget= self.content_widget,
            fn = Session.team_service.create_team,
            args= (team_name,),
            on_success=_success,
            on_error=_error
        )


# -- LAYOUT STUFF --

    def _refresh(self):
        Session.init_team_data()

        self.status_label.setText("")

        # grabbing team aesthetics
        self.my_username = Session.user
        self.my_user_id = Session.user_id
        self.my_team_name = Session.current_team_name
        self.my_team_standings = Session.my_team_standings
        
        self.my_next_pick = Session.next_pick
        self.is_draft_complete = Session.draft_complete
        self.is_league_locked = Session.is_league_locked

        self._update_view()

    def _update_view(self):
        self._update_player_slots()

        if bool(self.my_team_name):
            self.team_creator.setVisible(False)
            self.team_info.setVisible(True)
            self.team_overview.setVisible(True)
        else:
            self.team_creator.setVisible(True)
            self.team_info.setVisible(False)
            self.team_overview.setVisible(False)

        self.draft_picker.setVisible(
            bool(self.my_team_name) and not self.is_draft_complete and self.my_username == self.my_next_pick and self.is_league_locked
        )

        self.team_name_label.setText(f"{self.my_team_name}")

    def _update_player_slots(self):
        players = self.my_team_standings.get("players", []) if self.my_team_standings else []
        players.sort(key=lambda p: (p["left_at"] is not None, -datetime.fromisoformat(p["left_at"]).timestamp() if p["left_at"] else 0))

        # clear old slots
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
                slot = self._build_empty_player_slot()
            self.team_bar_layout.addWidget(slot, stretch=1)

        # default to first player
        if players:
            self._update_player_stat(players[0])

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #7a7a7a;")
        separator.setFixedHeight(2)
        separator.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        return separator
    
    def _set_status(self, msg, code=0):
        colors = {0: "#333", 1: "#2e7d32", 2: "#cc0000"}
        self.status_label.setStyleSheet(f"color: {colors.get(code, '#333')};")
        self.status_label.setText(msg)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
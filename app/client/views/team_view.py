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

        # root layout: defined here to use in other private methods
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        # clears then builds ui
        self._refresh_view()


    def _build_main(self):
        self.root_layout.addWidget(HeaderBar(self.app))

        # grabbing cached data
        self.username = Session.user
        self.user_id = Session.user_id
        self.team_name = Session.current_team_name
        self.next_pick = Session.next_pick
        self.draft_complete = Session.draft_complete
        self.my_team_standings = Session.my_team_standings

        # main content
        self.content_widget = QWidget()

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(35)

        # status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
        """)

        # adding layouts to main content
        if self.team_name != None:
            content_layout.addWidget(self._build_my_info())
            content_layout.addWidget(self._create_separator())
            if self.next_pick == self.username and self.draft_complete == False:
                content_layout.addWidget(self._build_draft_pick())
                content_layout.addWidget(self._create_separator())
            content_layout.addWidget(self._build_my_team())
            content_layout.addWidget(self._create_separator())
            content_layout.addWidget(self._build_player_stat_list())
        else:
            content_layout.addWidget(self._build_team_creator())
            content_layout.addWidget(self.status_label)

        # scrollable if required
        scrollable = QScrollArea()
        scrollable.setWidgetResizable(True)
        scrollable.setWidget(self.content_widget)

        # composing root
        self.root_layout.addWidget(scrollable, stretch=1)
        self.root_layout.addWidget(FooterNav(self.app))


    def _build_team_creator(self):
        create_cont = QWidget()

        main_layout = QVBoxLayout(create_cont)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        main_layout.addWidget(create_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(create_layout)
        
        return create_cont

    def _build_my_info(self):
        info_cont = QWidget()
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        team_label = QLabel(f"{self.team_name}")
        team_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        team_label.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold; 
            color: #333; 
        """)

        info_layout.addWidget(team_label)
        info_layout.addWidget(self.status_label)

        return info_cont

    def _build_draft_pick(self):
        pick_cont = QWidget()

        main_layout = QVBoxLayout(pick_cont)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pick_input = QComboBox()
        player_names = [p["name"] for p in Session.player_scores]
        player_names_sorted = sorted(player_names, key=str.casefold)
        self.pick_input.addItems(player_names_sorted)
        self.pick_input.setEditable(True)
        self.pick_input.setPlaceholderText("Blaz, MenaRD, Leshar...")

        pick_group_layout = QVBoxLayout()
        pick_group_layout.addWidget(self.pick_input)

        pick_group = QGroupBox("Pick a Player!")
        pick_group.setLayout(pick_group_layout)

        pick_label = QLabel("It's your turn to pick a player!")
        pick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pick_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333; 
        """)

        pick_btn = QPushButton("Pick")
        pick_btn.setFixedWidth(100)
        pick_btn.setFixedHeight(30)
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_btn.setStyleSheet("""
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
        pick_btn.clicked.connect(self.pick_player)

        pick_layout = QHBoxLayout()
        pick_layout.addWidget(pick_group, stretch=1)
        pick_layout.addWidget(pick_btn, stretch=1)
        pick_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(pick_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(pick_layout)
        
        return pick_cont
    
    def _build_my_team(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # Player row
        players_row = QHBoxLayout()
        players_row.setSpacing(10)
        players_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        players = self.my_team_standings.get("players", []) if self.my_team_standings else []
        players.sort(
            key=lambda p: (
                p["left_at"] is not None, 
                -datetime.fromisoformat(p["left_at"]).timestamp() if p["left_at"] else 0
            )
        )

        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
            else:
                slot = self._build_empty_player_slot()

            players_row.addWidget(slot, stretch=1)

        layout.addLayout(players_row)
        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        image = QLabel()
        image.setStyleSheet("border: 2px solid #333;")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

    def _build_player_stat_list(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(50, 0, 0, 0)
        layout.setSpacing(30)

        PLAYER_IMG_DIR = Path("app/client/assets/player_pictures")
        REGION_ICO_DIR = Path("app/client/assets/icons/flags")

        players = self.my_team_standings.get("players", []) if self.my_team_standings else []
        players.sort(
            key=lambda p: (
                p["left_at"] is not None, 
                -datetime.fromisoformat(p["left_at"]).timestamp() if p["left_at"] else 0
            )
        )
        for player in players:
            if not player:
                continue

            name = player["id"]
            region = player.get("region", "Unknown")
            points = player["points"]
            joined_at = player["joined_at"]
            left_at = player["left_at"]
            active = left_at is None

            # row container
            row = QFrame()
            row.setObjectName("playerRow")  # unique identifier

            row.setStyleSheet("""
                QFrame#playerRow {
                    border: 2px solid #aaaaaa;
                    border-radius: 4px;
                }
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(20, 20, 20, 20)
            row_layout.setSpacing(10)

            # --- Player image ---
            image = QLabel()
            image.setFixedSize(200, 200)
            image.setStyleSheet("border: 5px solid #333;")

            img_path = PLAYER_IMG_DIR / f"{name}.jpg"
            if not img_path.exists():
                img_path = PLAYER_IMG_DIR / "placeholder.png"

            pixmap = QPixmap(str(img_path))
            image.setPixmap(
                pixmap.scaled(
                    200,
                    200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            info_col = QVBoxLayout()
            info_col.setSpacing(0)
            info_col.setContentsMargins(0,25,0,25)

            img_path = REGION_ICO_DIR / f"{region}.png"
            if not img_path.exists():
                img_path = REGION_ICO_DIR / "placeholder.png"

            info_label = QLabel()
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setText(
                "<div style='line-height: 1.2;'>"
                f"<span style='font-size:24px; font-weight: bold; color:#333;'>{name}</span><br/>"
                f"<span style='font-size:16px; color:#777;'>{region}  </span>"
                f"<img src='{img_path}' width='18' height='12'> "
                "</div"
            )
            info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            points_label = QLabel(f"Points: {points}")
            points_label.setStyleSheet("color: #333; font-size: 20px;")
            points_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

            joined_label = QLabel(f"Joined At: {joined_at.split("T")[0]}")
            joined_label.setStyleSheet("color: #333; font-size: 20px;")
            joined_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

            info_col.addWidget(info_label)
            info_col.addWidget(points_label)
            info_col.addWidget(joined_label)

            if not active:
                transferred = QLabel("Transferred") 
                transferred.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
                left_label = QLabel(f"Left At: {left_at.split("T")[0]}")
                left_label.setStyleSheet("color: #333; font-size: 20px;")
                left_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

                info_col.addWidget(transferred)
                info_col.addWidget(left_label)

            # --- Assemble row ---
            row_layout.addWidget(image)
            row_layout.addLayout(info_col, stretch=1)
            row_layout.addStretch()

            layout.addWidget(row)
        
        return container


    def pick_player(self):
        player = self.pick_input.currentText()
        print("pick_player: CLICK")

        if not player:
            self._set_status("Please enter a player name.", status_type="e")
            return
        
        if not any(p["name"] == player for p in Session.player_scores):
            self._set_status(f"{player} not found. Names are case sensitive!", status_type="e")
            return
        
        def _success(success):
            if success:
                self._refresh_view()
                self._set_status(f"Welcome {player} to {self.team_name}!", status_type="s")
        
        def _error(error):
            self._set_status(f"Failed to pick player: {error}", status_type="e")
        
        self._set_status("Picking player...", status_type="p")
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
            self._set_status("Please enter a team name.", status_type="e")
        
        def _success(success):
            if success:
                self._refresh_view()
                self._set_status("Team created successfuly!", status_type="s")
        
        def _error(error):
            self._set_status(f"Failed to create team: {error}", status_type="e")
        
        self._set_status("Creating team...", status_type="p")
        run_async(
            parent_widget= self.content_widget,
            fn = Session.team_service.create_team,
            args= (team_name,),
            on_success=_success,
            on_error=_error
        )

    def _refresh_view(self):
        self._clear_layout(self.layout())
        Session.init_aesthetics()
        self._build_main()

    def _clear_layout(self, layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

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

    def _set_status(self, msg, status_type=None):
        self.status_label.setText(msg)

        if status_type == "s":
            color = "#2e7d32"
        elif status_type == "e":
            color = "#cc0000"
        else:
            color = "#333333"

from pathlib import Path

from functools import partial
import sys
import uuid

from PyQt6.QtWidgets import (
    QWidget, 
    QLabel, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLineEdit,
    QGroupBox,
    QFrame,
    QSizePolicy,
    QScrollArea,
)

from PyQt6.QtCore import Qt

from PyQt6.QtGui import QPixmap

from app.client.controllers.session import Session

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

from app.services.app_store import AppStore

class LeaderboardView(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.PLAYER_IMG_DIR = Path(self.resource_path("app/client/assets/player_pictures"))
        
        # build static ui then update
        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.header.refresh_button.refresh_requested.connect(lambda: self._refresh(force=1))
        
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
        self.info = self._build_info()
        self.leaguemate_container = self._build_leaguemates()
        self.favourite_container = self._build_favourites()


        self.content_layout.addWidget(self.info)
        self.content_layout.addWidget(self.leaguemate_container)
        self.content_layout.addWidget(self.favourite_container)


# -- BUILDERS --

    def _build_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        leaderboards = QLabel(f"Leaderboards")
        leaderboards.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaderboards.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold; 
            color: #333; 
        """)

        layout.addWidget(leaderboards)
        layout.addWidget(self._create_separator())

        return container
    
    def _build_leaguemates(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.leaguemate_layout = QVBoxLayout()
        self.leaguemate_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(self.leaguemate_layout)
        layout.addWidget(self._create_separator())

        return container

    def _build_favourites(self):
        container = QWidget()

        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(15)

        title_label = QLabel(f"Favourite users")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #333; 
        """)

        self.add_fav_input = QLineEdit()
        self.add_fav_input.setPlaceholderText("User ID")

        add_fav_layout = QVBoxLayout()
        add_fav_layout.addWidget(self.add_fav_input)

        add_fav_group = QGroupBox("Pick a User!")
        add_fav_group.setLayout(add_fav_layout)

        add_fav_label = QLabel("Add a favourite user here!")
        add_fav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_fav_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333; 
        """)

        btn = QPushButton("Favourite")
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
        btn.clicked.connect(self.add_favourite)

        add_layout = QHBoxLayout()
        add_layout.addWidget(add_fav_group, stretch=1)
        add_layout.addWidget(btn, stretch=1)
        add_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.favourite_display = QVBoxLayout()
        self.favourite_display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        main_layout.addWidget(title_label)
        main_layout.addLayout(add_layout)
        main_layout.addWidget(self._create_separator())
        main_layout.addLayout(self.favourite_display)

        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        image = QLabel()
        image.setStyleSheet("border: 2px solid #333;")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        player_name = player["player_name"]
        img_path = self.PLAYER_IMG_DIR / f"{player_name}.jpg"

        pixmap = QPixmap(str(img_path))
        if pixmap.isNull():
            pixmap = QPixmap(str(self.PLAYER_IMG_DIR / "placeholder.png"))

        image.setPixmap(
            pixmap.scaled(
                140, 140,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        name = QLabel(player["player_name"])
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
        layout.setSpacing(5)

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

    def _build_team_widget(self, team: dict) -> QWidget:
        """
        Builds a QFrame representing one team in the leaderboard.
        """
        team_frame = QFrame()
        team_frame.setObjectName("teamFrame")
        team_frame.setStyleSheet("""
            QFrame#teamFrame {
                border: 2px solid #aaaaaa;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(team_frame)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Team info labels
        owner_label = QLabel(f"Owner: {team['user_name']}")
        name_label = QLabel(f"Team Name: {team['team_name']}")
        points_label = QLabel(f"Total Points: {team['total_points']}")

        layout.addWidget(owner_label)
        layout.addWidget(name_label)
        layout.addWidget(points_label)

        # Player row
        player_row = QHBoxLayout()
        player_row.setSpacing(5)
        player_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        players = team.get("players", [])

        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
            else:
                slot = self._build_empty_player_slot()
            player_row.addWidget(slot, stretch=1)

        layout.addLayout(player_row)
        return team_frame

    def _build_favourite_widget(self, team: dict) -> QWidget:
        """
        Builds a single favourite team row with remove button.
        """
        fav_frame = QFrame()
        fav_frame.setObjectName("favFrame")
        fav_frame.setStyleSheet("""
            QFrame#favFrame {
                border: 2px solid #aaaaaa;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(fav_frame)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Info labels
        owner_label = QLabel(f"Owner: {team['user_name']}")
        name_label = QLabel(f"Team Name: {team['team_name']}")
        points_label = QLabel(f"Total Points: {team['total_points']}")

        layout.addWidget(owner_label)
        layout.addWidget(name_label)
        layout.addWidget(points_label)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedSize(60, 40)
        remove_btn.clicked.connect(partial(self.remove_favourite, team["user_id"]))
        layout.addWidget(remove_btn)

        # Player row
        player_row = QHBoxLayout()
        player_row.setSpacing(5)
        player_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        players = team.get("players", [])
        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
            else:
                slot = self._build_empty_player_slot()
            player_row.addWidget(slot, stretch=1)

        layout.addLayout(player_row)
        return fav_frame


# -- BUTTON METHODS --

    def add_favourite(self):
        print("add_favourite: CLICK")
        fav = self.add_fav_input.text().strip()

        try:
            uuid.UUID(str(fav))
        except ValueError:
            self._set_status("Please enter a valid user ID", 2)
            return

        if not fav:
            self._set_status("Please enter a user ID.", 2)
            return

        try:
            AppStore.append("favourites", fav)
            self.add_fav_input.setText("")
            self._refresh(force=1)
            self._set_status("Favourite added!", 1)

        except Exception as e:
            self._set_status(f"Unable to add favourite: {e}", 2)

    def remove_favourite(self, user_id):
        try:
            AppStore.remove("favourites", user_id)
            self._refresh(force=1)
            self._set_status("Favourite removed!", 1)
        except Exception as e:
            self._set_status(f"Unable to remove favourite: {e}", 2)


# -- LAYOUT STUFF --

    def _refresh(self, force=0):
        Session.init_leaderboards(force)
        Session.init_favourites(force)

        self.status_label.setText("")

        self.my_username = Session.user
        self.my_user_id = Session.user_id
        self.leaguemate_data = Session.leaguemate_standings
        self.favourite_data = Session.favourite_standings
        self.my_league = Session.current_league_name

        self._update_view()

    def _update_view(self):
        self._update_leaguemates()
        self._update_favourites()

    def _update_leaguemates(self):
        for i in reversed(range(self.leaguemate_layout.count())):
            widget = self.leaguemate_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.leaguemate_data:
            self.leaguemate_container.setVisible(True)
            for team in sorted(self.leaguemate_data, key=lambda t: t["total_points"], reverse=True):
                team_widget = self._build_team_widget(team)
                self.leaguemate_layout.addWidget(team_widget)
        else:
            self.leaguemate_container.setVisible(False)

    def _update_favourites(self):
        for i in reversed(range(self.favourite_display.count())):
            widget = self.favourite_display.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.favourite_data:
            for team in sorted(self.favourite_data, key=lambda t: t["total_points"], reverse=True):
                fav_widget = self._build_favourite_widget(team)
                self.favourite_display.addWidget(fav_widget)

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

    def resource_path(self, relative_path: str) -> str:
        if hasattr(sys, "_MEIPASS"):
            return str(Path(sys._MEIPASS) / relative_path)
        return str(Path(relative_path).resolve())
from pathlib import Path

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

from app.client.controllers.async_runner import run_async
from app.client.controllers.session import Session

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

from app.services.app_store import AppStore

class LeaderboardView(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app

        # root layout: defined here to use in other private methods
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        # grab leaderboard data
        Session.init_leaderboards()
        Session.init_favourites()
        self.leaguemate_data = Session.leaguemate_standings
        self.favourite_data = Session.favourite_standings
        self.my_league = Session.current_league_name

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
        self.my_team_data = Session.my_team_data


        # main content
        self.content_widget = QWidget()

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(40, 35, 40, 35)
        content_layout.setSpacing(35)


        # add to main widget here
        content_layout.addWidget(self._build_info())
        content_layout.addWidget(self._create_separator())
        content_layout.addWidget(self._build_league_teams())
        content_layout.addWidget(self._create_separator())
        content_layout.addWidget(self._build_favourites())

        # scrollable if required
        scrollable = QScrollArea()
        scrollable.setWidgetResizable(True)
        scrollable.setWidget(self.content_widget)

        # composing root
        self.root_layout.addWidget(scrollable, stretch=1)
        self.root_layout.addWidget(FooterNav(self.app))


    def _build_info(self):
        info_cont = QWidget()
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        leaderboards = QLabel(f"Leaderboards")
        leaderboards.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaderboards.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold; 
            color: #333; 
        """)

        info_layout.addWidget(leaderboards)

        return info_cont
    
    def _build_league_teams(self):
        self.leaguemate_data_sorted = sorted(self.leaguemate_data, key=lambda t: t["total_points"])

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        leaguemates = QLabel(f"Standings within {self.my_league}")
        leaguemates.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaguemates.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #333; 
        """)

        layout.addWidget(leaguemates)

        for team in self.leaguemate_data_sorted:
            # team box
            team_frame = QFrame()
            team_frame.setObjectName("teamFrame")  # unique identifier
            team_frame.setStyleSheet("""
                QFrame#teamFrame {
                    border: 2px solid #aaaaaa;
                    border-radius: 4px;
                }
            """)
            
            team_data = QVBoxLayout(team_frame)
            team_data.setSpacing(10)
            team_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # player row
            players_row = QHBoxLayout()
            players_row.setSpacing(10)
            players_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

            owner = QLabel(f"Owner: {team["user_name"]}")
            name = QLabel(f"Team Name: {team["team_name"]}")
            points = QLabel(f"Total Points: {team["total_points"]}")
            
            team_players = team["players"]

            for i in range(5):
                if i < len(team_players):
                    slot = self._build_player_slot(team_players[i])
                else:
                    slot = self._build_empty_player_slot()

                players_row.addWidget(slot, stretch=1)

            team_data.addWidget(owner)
            team_data.addWidget(name)
            team_data.addWidget(points)
            team_data.addLayout(players_row)
            
            layout.addWidget(team_frame)
        
        return container

    def _build_favourites(self):

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        favourites = QLabel(f"Favourite users")
        favourites.setAlignment(Qt.AlignmentFlag.AlignCenter)
        favourites.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #333; 
        """)

        layout.addWidget(favourites)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
        """)
        self._set_status("Check your favourite users here!")

        layout.addWidget(self.status_label)

        create_cont = QWidget()

        main_layout = QVBoxLayout(create_cont)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        main_layout.addSpacing(15)
        main_layout.addWidget(add_fav_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(add_layout)

        layout.addWidget(create_cont)
        
        if self.favourite_data:
            self.favourite_data_sorted = sorted(self.favourite_data, key=lambda t: t["total_points"])
            for team in self.favourite_data_sorted:
                # team box
                team_frame = QFrame()
                team_frame.setObjectName("teamFrame")  # unique identifier
                team_frame.setStyleSheet("""
                    QFrame#teamFrame {
                        border: 2px solid #aaaaaa;
                        border-radius: 4px;
                    }
                """)
                
                team_data = QVBoxLayout(team_frame)
                team_data.setSpacing(10)
                team_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # player row
                players_row = QHBoxLayout()
                players_row.setSpacing(10)
                players_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

                owner = QLabel(f"Owner: {team["user_name"]}")
                owner_id = QLabel(f"Owner ID: {team["user_id"]}")
                name = QLabel(f"Team Name: {team["team_name"]}")
                points = QLabel(f"Total Points: {team["total_points"]}")

                remove = QPushButton("Remove")
                remove.setFixedSize(60, 40)
                remove.clicked.connect(lambda: self.remove_favourite(team["user_id"]))
                
                team_players = team["players"]

                for i in range(5):
                    if i < len(team_players):
                        slot = self._build_player_slot(team_players[i])
                    else:
                        slot = self._build_empty_player_slot()

                    players_row.addWidget(slot, stretch=1)

                team_data.addWidget(owner)
                team_data.addWidget(name)
                team_data.addWidget(points)
                team_data.addWidget(remove)
                team_data.addLayout(players_row)
                
                layout.addWidget(team_frame)
        
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
        player_name = player["player_name"]
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


    def add_favourite(self):
        print("add_favourite: CLICK")
        fav = self.add_fav_input.text().strip()

        if not fav:
            self._set_status("Please enter a user ID.", status_type="e")

        try:
            AppStore.append("favourites", fav)
            self._set_status("Favourite added!", status_type="s")
            Session.init_favourites()
            self.favourite_data = Session.favourite_standings
            self._refresh_view()

        except Exception as e:
            self._set_status(f"Unable to add favourite: {e}", status_type="e")

    def remove_favourite(self, user_id):
        try:
            AppStore.remove("favourites", user_id)
            self._set_status("Favourite removed!")
            Session.init_favourites()
            self.favourite_data = Session.favourite_standings
            self._refresh_view()
        except Exception as e:
            self._set_status(f"Unable to remove favourite: {e}", status_type="e")


    def _refresh_view(self):
        self._clear_layout(self.layout())
        Session.init_aesthetics()
        Session.init_leaderboards()
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

        self.status_label.setStyleSheet(f"color: {color};")
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap
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
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar

class LeaderboardView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.RANK_STYLES = {
            1: "#FFD700",
            2: "#C0C0C0",
            3: "#CD7F32",
            4: "#888888",
            5: "#FF4D4D",
        }
        
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(SCROLL_STYLESHEET)

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(10)

        scroll.setWidget(self.content_widget)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(25)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
            }
        """)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(scroll, stretch=1)
        self.root_layout.addWidget(self.status_label)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        self.info = self._build_info()
        self.leaguemate_container = self._build_leaguemates()


        self.content_layout.addWidget(self.info)
        self.content_layout.addWidget(self.leaguemate_container)


# -- BUILDERS --

    def _build_info(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        players = QPushButton("Player Pool")
        players.setCursor(Qt.CursorShape.PointingHandCursor)
        players.clicked.connect(self.app.show_players_view)
        players.setStyleSheet(BUTTON_STYLESHEET_A)

        globals_btn = QPushButton("Global Stats")
        globals_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        globals_btn.clicked.connect(self.app.show_globals_view)
        globals_btn.setStyleSheet(BUTTON_STYLESHEET_A)

        leaderboards = QLabel("Leaderboards")
        leaderboards.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaderboards.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold;
        """)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(leaderboards, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch()
        right_layout.addWidget(players, alignment=Qt.AlignmentFlag.AlignTop)

        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(globals_btn, alignment=Qt.AlignmentFlag.AlignTop)
        left_layout.addStretch()

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        return container
    
    def _build_leaguemates(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.leaguemate_layout = QVBoxLayout()
        self.leaguemate_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(self.leaguemate_layout)

        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(5)

        image = QLabel()
        image.setFixedSize(QSize(150, 150))
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        name = QLabel()
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
        """)

        if player:
            # --- Player present ---
            player_name = player.get("player_name", "-")
            img_path = ResourcePath.PLAYERS / f"{player_name}.jpg"

            pixmap = QPixmap(str(img_path))
            if pixmap.isNull():
                pixmap = QPixmap(str(ResourcePath.PLAYERS / "placeholder.png"))

            image.setPixmap(
                pixmap.scaled(
                    150, 150,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            name.setText(player_name)
            image.setStyleSheet("border: 2px solid #BBBBBB;")

        else:
            # --- Empty slot ---
            image.setStyleSheet("""
                border: 2px dashed #555;
                background-color: #333;
                color: #eee;
            """)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setText("?")

            name.setText("-")
            name.setStyleSheet("""
                font-size: 16px; 
                font-weight: bold; 
                color: #999; 
            """)

        layout.addWidget(image)
        layout.addWidget(name)

        return slot

    def _build_team_widget(self, team: dict) -> QWidget:
        team_frame = QFrame()
        team_frame.setObjectName("teamFrame")
        team_frame.setStyleSheet("""
            QFrame#teamFrame {
                border: 2px solid #555555;
                border-radius: 4px;
            }
        """)

        root_layout = QVBoxLayout(team_frame)
        root_layout.setSpacing(15)

        user_cont = QWidget()
        user = QHBoxLayout(user_cont)
        user.setSpacing(15)
        user.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        avatar = self._build_avatar(team["user_id"], 250)
        avatar.setStyleSheet("border: 3px solid #FFFFFF; border-radius: 5px;")
        avatar.setFixedSize(250, 250)

        info_cont = QWidget()
        info_cont.setFixedWidth(300)
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        rank = team.get("rank", 999)
        rank_color = self.RANK_STYLES.get(rank, "#FFFFFF")

        owner_label = QLabel(f"#{rank} {team['user_name']}")
        owner_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 50px;
            color: {rank_color};
        """)

        if rank <= 3:
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(25)
            glow.setColor(QColor(rank_color))
            glow.setOffset(0, 0)
            owner_label.setGraphicsEffect(glow)

        name_label = QLabel(f"{team['team_name']}")
        name_label.setStyleSheet('''
            font-weight: bold;
            font-size: 28px;
        ''')
        points_label = QLabel(f"Total Points: {team['total_points']}")

        info_layout.addStretch()
        info_layout.addWidget(owner_label, alignment= Qt.AlignmentFlag.AlignHCenter)
        info_layout.addWidget(name_label, alignment= Qt.AlignmentFlag.AlignHCenter)
        info_layout.addStretch()
        info_layout.addWidget(points_label, alignment= Qt.AlignmentFlag.AlignHCenter)
        info_layout.addStretch()

        user.addStretch()
        user.addWidget(avatar)
        user.addStretch()
        user.addWidget(info_cont)
        user.addStretch()

        player_row = QHBoxLayout()
        player_row.setSpacing(5)
        player_row.setContentsMargins(25, 0, 25, 0)
        player_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        players = team.get("players", [])

        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
            else:
                slot = self._build_player_slot({})

            player_row.addWidget(slot, stretch=1)

        root_layout.addWidget(user_cont)
        root_layout.addLayout(player_row)

        return team_frame

    def _build_avatar(self, user_id, size):
        image = QLabel()
        avatar = QPixmap()

        try:
            avatar.loadFromData(Session.init_avatar(user_id))
            if avatar.isNull():
                avatar = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        except Exception:
            avatar = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        image.setPixmap(
            avatar.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        
        return image

# -- LAYOUT STUFF --

    def _refresh(self, force=0):
        Session.init_leaderboards(force)

        self.status_label.setText("")

        self.my_username = Session.user
        self.my_user_id = Session.user_id
        self.leaguemate_data = Session.leaguemate_standings

        self._update_view()

    def _update_view(self):
        self._update_leaguemates()

    def _update_leaguemates(self):
        while self.leaguemate_layout.count():
            item = self.leaguemate_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if self.leaguemate_data:
            self.leaguemate_container.setVisible(True)

            sorted_teams = sorted(
                self.leaguemate_data,
                key=lambda t: t["total_points"],
                reverse=True
            )

            ranked_teams = self._apply_ranks(sorted_teams)

            for team in ranked_teams:
                team_widget = self._build_team_widget(team)
                self.leaguemate_layout.addWidget(team_widget)

        else:
            label = QLabel("It's quiet. Too quiet...\n\nMaybe join a league?")
            self.leaguemate_layout.addSpacerItem(QSpacerItem(10,100))
            self.leaguemate_layout.addWidget(label, alignment= Qt.AlignmentFlag.AlignVCenter)

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

    def _apply_ranks(self, teams):
        ranked = []

        last_points = None
        last_rank = 0

        for i, team in enumerate(teams):
            pts = team.get("total_points", 0)

            if pts == last_points:
                rank = last_rank
            else:
                rank = i + 1
                last_rank = rank
                last_points = pts

            team = dict(team)
            team["rank"] = rank
            ranked.append(team)

        return ranked

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

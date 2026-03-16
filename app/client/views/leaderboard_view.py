from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.misc import _build_empty_label, fit_text_to_width
from app.client.widgets.hover_image import HoverImage

class LeaderboardView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.connect_refresh(lambda: self._refresh(force=1))

        self.RANK_STYLES = {
            1: "#FFD700",
            2: "#C0C0C0",
            3: "#CD7F32",
            4: "#FF4D4D",
            5: "#FF4D4D",
        }
        
        # build static ui then update
        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(30)

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

        self.root_layout.addWidget(scroll, stretch=1)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        self.leaguemate_container = self._build_leaguemates()

        self.content_layout.addWidget(self._build_info())
        self.content_layout.addWidget(self.status_label)
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

    def _build_team_widget(self, team: dict) -> QWidget:
        team_frame = QFrame()
        team_frame.setObjectName("teamFrame")
        team_frame.setStyleSheet("""
            QFrame#teamFrame {
                background-color: #090E2B;
                border: 2px solid #444444;
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
        info_cont.setFixedWidth(500)
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        rank = team.get("rank", 999)
        rank_color = self.RANK_STYLES.get(rank, "#FFFFFF")

        owner_label = QLabel()
        owner_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 50px;
            color: {rank_color};
        """)
        fit_text_to_width(owner_label, f"#{rank} {team['user_name']}", 500, max_font_size=50)

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
        user.addWidget(info_cont, stretch=1)
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
        image.setPixmap(
            Session.get_pixmap("avatars", str(user_id)).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        return image

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
        name.setStyleSheet("font-size: 16px; font-weight: bold;")

        points = QLabel()
        points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        points.setStyleSheet("font-size: 14px; font-weight: bold;")

        if player:
            player_name = player.get("player_name", "-")
            player_points = str(player.get("points", "-"))

            pixmap = Session.get_pixmap("players", player_name)
            image = HoverImage(pixmap, size=150, border_width=2, border_color="#BBBBBB")
            
            name.setText(player_name)
            points.setText(player_points)
        else:
            image.setStyleSheet("""
                border: 2px dashed #555;
                background-color: #333;
                color: #eee;
            """)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setText("?")
            name.setText("-")
            name.setStyleSheet("font-size: 16px; font-weight: bold; color: #999;")
            points.setText("-")
            points.setStyleSheet("font-size: 14px; font-weight: bold; color: #999;")

        layout.addWidget(image)
        layout.addWidget(name)
        layout.addWidget(points)
        return slot

# -- LAYOUT STUFF --

    def _refresh(self, force=0):
        Session.init_leaderboards(force)

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
            self.leaguemate_layout.addSpacerItem(QSpacerItem(10,100))
            self.leaguemate_layout.addWidget(_build_empty_label(), alignment= Qt.AlignmentFlag.AlignVCenter)

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

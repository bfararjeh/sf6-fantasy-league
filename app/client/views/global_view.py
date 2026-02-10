from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar

class GlobalView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        self.global_stats = Session.global_stats or []

        self._build_main()

    def _build_main(self):
        self.root_layout.addWidget(HeaderBar(self.app))

        # main content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(10)

        # scrollable if required
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidget(content_widget)

        # composing content
        content_layout.addWidget(self._build_title())
        if bool(self.global_stats):
            content_layout.addWidget(self._build_stats(self.global_stats[0]))
        else:
            cont = QWidget()
            layout = QVBoxLayout(cont)
            layout.setContentsMargins(25,0,25,0)

            main = QLabel("""
            It's quiet. Too quiet...
            """)
            main.setWordWrap(True)
            main.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addStretch()
            layout.addWidget(main)
            layout.addStretch()

            content_layout.addWidget(cont)

        # composing root
        self.root_layout.addWidget(scroll, stretch=1)
        self.root_layout.addWidget(FooterNav(self.app))

    def _build_title(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        players = QPushButton("Player Pool")
        players.setCursor(Qt.CursorShape.PointingHandCursor)
        players.clicked.connect(self.app.show_players_view)
        players.setStyleSheet(BUTTON_STYLESHEET_A)

        leaderboards = QPushButton("Leaderboards")
        leaderboards.setCursor(Qt.CursorShape.PointingHandCursor)
        leaderboards.clicked.connect(self.app.show_leaderboards_view)
        leaderboards.setStyleSheet(BUTTON_STYLESHEET_A)

        global_stats = QLabel("Global Stats")
        global_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        global_stats.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold;
        """)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(global_stats, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch()
        right_layout.addWidget(players, alignment=Qt.AlignmentFlag.AlignTop)

        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(leaderboards, alignment=Qt.AlignmentFlag.AlignTop)
        left_layout.addStretch()

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        return container

    def _build_stats(self, stats: dict):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        def add_row(grid, row_idx, name, value):
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            name_label.setStyleSheet("font-weight: bold;")

            value_label = QLabel(value)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            grid.addWidget(name_label, row_idx, 0)
            grid.addWidget(value_label, row_idx, 1)

        best_team = stats.get("best_scoring_team", {})
        if best_team:
            layout.addWidget(self._build_best_team(best_team))

        # main stats
        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(20)
        main_grid.setVerticalSpacing(5)
        row = 0

        add_row(main_grid, row, "Total Number of Managers:", str(stats.get("managers_count", 0)))
        row += 1
        add_row(main_grid, row, "Total Number of Leagues:", str(stats.get("leagues_count", 0)))
        row += 1
        add_row(main_grid, row, "Unique Players Picked:", str(stats.get("unique_players_picked", 0)))
        row += 1

        layout.addLayout(main_grid)
        layout.addWidget(self._build_regions("Points by Region", stats.get('players_by_region', [])))

        most_picked = stats.get("most_picked_players", [])
        layout.addWidget(self._build_frequency_picked("Most Picked Players", most_picked))

        least_picked = stats.get("least_picked_players", [])
        layout.addWidget(self._build_frequency_picked("Least Picked Players", least_picked))

        return container

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

    def _build_best_team(self, best_team):
        team_frame = QFrame()
        team_frame.setObjectName("teamFrame")
        team_frame.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        team_frame.setStyleSheet("""
            QFrame#teamFrame {
                border: 2px solid #555555;
                border-radius: 4px;
            }
        """)

        cont = QWidget()
        top_team_layout = QHBoxLayout(cont)
        top_team_layout.setSpacing(15)

        # top team
        user = QHBoxLayout(team_frame)
        user.setSpacing(15)
        user.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        avatar = self._build_avatar(best_team["user_id"], 200)
        avatar.setStyleSheet("border: 3px solid #FFFFFF; border-radius: 5px;")
        avatar.setFixedSize(200, 200)

        info_cont = QWidget()
        info_cont.setFixedWidth(300)
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        owner_label = QLabel(f"#1 {best_team['username']}")
        owner_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 50px;
            color: #FFD700;
        """)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setColor(QColor("#FFD700"))
        glow.setOffset(0, 0)
        owner_label.setGraphicsEffect(glow)

        name_label = QLabel(f"{best_team['teamname']}")
        name_label.setStyleSheet('''
            font-weight: bold;
            font-size: 28px;
        ''')
        points_label = QLabel(f"{best_team['total_points']}pts")
        points_label.setStyleSheet("font-weight: bold; font-size: 24px; ")

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
        
        scorer = QLabel("Global Best Team:")
        scorer.setStyleSheet("font-weight: bold; font-size: 32px; ")
        scorer.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        center = QWidget()
        centlay = QVBoxLayout(center)
        centlay.setSpacing(10)
        centlay.addWidget(scorer)
        centlay.addWidget(team_frame)

        top_team_layout.addStretch()
        top_team_layout.addWidget(center, alignment=Qt.AlignmentFlag.AlignHCenter)
        top_team_layout.addStretch()

        return cont

    def _build_regions(self, title: str, regions: list) -> QWidget:
        # Toggle button (section header)
        toggle = QPushButton(title)
        toggle.setStyleSheet(BUTTON_STYLESHEET_A)
        toggle.setCheckable(True)
        toggle.setChecked(False)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        # Content container
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setContentsMargins(10, 5, 10, 5)
        content_layout.setHorizontalSpacing(20)
        content_layout.setVerticalSpacing(15)

        max_cols = 3
        row, col = 0, 0

        regions_sorted = sorted(
            regions,
            key=lambda r: (
                r.get("total_points", 0) == 0,
                -r.get("total_points", 0),
                r.get("region", "")
            )
        )

        for region_data in regions_sorted:
            region_name = region_data.get("region", "Unknown")
            total_points = region_data.get("total_points", 0)

            # Flag
            flag_path = ResourcePath.FLAGS / f"{region_name}.png"
            if not flag_path.exists():
                print(region_name)
                flag_path = ResourcePath.FLAGS / "placeholder.png"

            flag_pixmap = QPixmap(str(flag_path)).scaled(
                24, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            flag_label = QLabel()
            flag_label.setPixmap(flag_pixmap)

            # Region label with flag
            name_label = QLabel(region_name)
            name_label.setStyleSheet("font-weight: bold; font-size: 20px; ")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            top_row = QWidget()
            top_layout = QHBoxLayout(top_row)
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(5)
            top_layout.addStretch()
            top_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignVCenter)
            top_layout.addWidget(flag_label, alignment=Qt.AlignmentFlag.AlignVCenter)
            top_layout.addStretch()

            # Points label
            points_label = QLabel(f"{total_points} pts")
            points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Container for single grid cell
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(5, 5, 5, 5)
            cell_layout.setSpacing(5)
            cell_layout.addWidget(top_row)
            cell_layout.addWidget(points_label)

            content_layout.addWidget(cell, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Initially hide content
        content.setVisible(False)
        toggle.toggled.connect(content.setVisible)

        # Wrapper widget to hold both toggle button and content
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(25)
        wrapper_layout.addWidget(toggle)
        wrapper_layout.addWidget(content)

        return wrapper
    
    def _build_frequency_picked(self, title: str, players: list):
        """
        Build a collapsible section showing most or least picked players.
        Each player is a widget with avatar, name, and region/flag.
        """
        # Toggle button (acts like section header)
        toggle = QPushButton(title)
        toggle.setStyleSheet(BUTTON_STYLESHEET_A)
        toggle.setCheckable(True)
        toggle.setChecked(False)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        # Content container
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 5, 10, 5)
        content_layout.setSpacing(15)

        # Batch players into rows of 5
        batch_size = 5
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(20)

            for player in batch:
                name = player["player_name"]
                picked_count = player["pick_count"]

                # Player container
                player_cont = QWidget()
                player_layout = QVBoxLayout(player_cont)
                player_layout.setContentsMargins(0, 0, 0, 0)
                player_layout.setSpacing(5)

                # Avatar
                image = QLabel()
                image.setFixedSize(160, 160)
                image.setStyleSheet("border: 3px solid #BBBBBB;")
                image.setAlignment(Qt.AlignmentFlag.AlignCenter)

                img_path = ResourcePath.PLAYERS / f"{name}.jpg"
                pixmap = QPixmap(str(img_path))
                if pixmap.isNull():
                    pixmap = QPixmap(str(ResourcePath.PLAYERS / "placeholder.png"))

                image.setPixmap(
                    pixmap.scaled(
                        160, 160,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )

                info_label = QLabel()
                info_label.setTextFormat(Qt.TextFormat.RichText)
                info_label.setText(
                    "<div style='line-height: 1.5; text-align:center;'>"
                    f"<span style='font-size:20px; font-weight:bold'>{name}</span><br/>"
                    f"<span style='font-size:20px; font-weight:bold'>{picked_count}</span>"
                    "</div>"
                )
                info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

                # Assemble player widget
                player_layout.addWidget(image)
                player_layout.addWidget(info_label)
                row_layout.addWidget(player_cont)

            content_layout.addWidget(row)

        content.setVisible(False)
        toggle.toggled.connect(content.setVisible)

        # Wrap in a container layout
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(25)
        container_layout.addWidget(toggle)
        container_layout.addWidget(content)

        return container

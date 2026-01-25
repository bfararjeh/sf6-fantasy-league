from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, 
    QLabel,
    QVBoxLayout, 
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QPushButton
)

from PyQt6.QtCore import Qt

from PyQt6.QtGui import QPixmap

from app.client.controllers.session import Session

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

class PlayerView(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app

        # root layout: defined here to use in other private methods
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        # grab player info then cache it
        self.player_scores = Session.player_scores

        self.SORT_KEYS = {
            "name": lambda p: p["name"].lower(),
            "region": lambda p: p["region"].lower(),
            "points": lambda p: -p["cum_points"],
        }

        self.SORT_LABELS = {
            "name": "Sort: Name",
            "region": "Sort: Region",
            "points": "Sort: Points",
        }

        self._build_main()


    def _build_main(self):
        self.root_layout.addWidget(HeaderBar(self.app))

        # main content
        content_widget = QWidget()

        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(35)

        # player layout
        self.player_cont = QWidget()

        self.player_layout = QVBoxLayout(self.player_cont)
        self.player_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.player_layout.setContentsMargins(0, 0, 0, 0)
        self.player_layout.setSpacing(35)

        # adding widgets to main content wiget
        content_layout.addWidget(self._build_title())

        self._rebuild_players_view()

        content_layout.addWidget(self.player_cont)

        # scrollable if required
        scrollable = QScrollArea()
        scrollable.setWidgetResizable(True)
        scrollable.setWidget(content_widget)

        # composing root
        self.root_layout.addWidget(scrollable, stretch=1)
        self.root_layout.addWidget(FooterNav(self.app))

    def _build_title(self):
        info_cont = QWidget()
        info_cont.setObjectName("persistent")
        info_layout = QVBoxLayout(info_cont)
        info_layout.setSpacing(15)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        team_label = QLabel("Player Pool")
        team_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        team_label.setStyleSheet("""
            font-size: 64px; 
            font-weight: bold; 
            color: #333; 
        """)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #7a7a7a;")
        separator.setFixedHeight(2)
        separator.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.current_sort_index = 0
        self.current_sort = list(self.SORT_KEYS.keys())[self.current_sort_index]

        self.sort_btn = QPushButton(self.SORT_LABELS[self.current_sort])
        self.sort_btn.setFixedWidth(80)
        self.sort_btn.clicked.connect(self._cycle_sort_mode)

        info_layout.addWidget(team_label)
        info_layout.addWidget(separator)
        info_layout.addWidget(self.sort_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        return info_cont

    def _build_player_slot(self, player_batch):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        PLAYER_IMG_DIR = Path("app/client/assets/player_pictures")
        REGION_ICO_DIR = Path("app/client/assets/icons/flags")

        for player in player_batch:

            name = player["name"]
            region = player["region"]
            points = player["cum_points"]

            player_cont = QWidget()
            player_layout = QVBoxLayout(player_cont)
            player_layout.setContentsMargins(0, 0, 0, 0)
            player_layout.setSpacing(0)

            image = QLabel()
            image.setFixedSize(160, 160)
            image.setStyleSheet("border: 3px solid #333;")
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)

            img_path = PLAYER_IMG_DIR / f"{player["name"]}.jpg"

            pixmap = QPixmap(str(img_path))
            if pixmap.isNull():
                pixmap = QPixmap(str(PLAYER_IMG_DIR / "placeholder.png"))

            image.setPixmap(
                pixmap.scaled(
                    160, 160,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            img_path = REGION_ICO_DIR / f"{player["region"]}.png"
            if not img_path.exists():
                img_path = REGION_ICO_DIR / "placeholder.png"

            info_label = QLabel()
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setText(
                "<div style='line-height: 1;'>"
                f"<span style='font-size:20px; font-weight: bold; color:#333;'>{name}</span><br/>"
                f"<span style='font-size:16px; color:#888;'>{region}  </span>"
                f"<img src='{img_path}' width='18' height='12'><br/><br/>"
                f"<span style='font-size:16px; font-weight:bold; color:#333;'>{points}  </span>"
                "</div"
            )
            info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            player_layout.addWidget(image)
            player_layout.addWidget(info_label)
            layout.addWidget(player_cont)

        return row

    def _rebuild_players_view(self, sort_by="name"):
        self.built = True
        players = self.player_scores[:]

        players.sort(key=self.SORT_KEYS[sort_by])

        # clear layout
        for i in reversed(range(self.player_layout.count())):
            item = self.player_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                # skip the persistent container
                if widget.objectName() == "persistentContainer":
                    continue
                self.player_layout.takeAt(i)
                widget.deleteLater()

        # rebuild
        for i in range(0, len(players), 5):
            batch = players[i:i + 5]
            self.player_layout.addWidget(self._build_player_slot(batch))

    def _cycle_sort_mode(self):
        self.current_sort_index = (self.current_sort_index + 1) % len(self.SORT_KEYS)
        self.current_sort = list(self.SORT_KEYS.keys())[self.current_sort_index]

        self.sort_btn.setText(self.SORT_LABELS[self.current_sort])
        self._rebuild_players_view(sort_by=self.current_sort)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager
from app.client.theme import *
from app.client.widgets.hover_image import HoverImage

class QualifiedView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        self.players = Session.player_scores or []

        self._build_main()

    def _build_main(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 15, 50, 15)
        content_layout.setSpacing(50)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidget(content_widget)

        content_layout.addWidget(self._build_title())

        # only qualified players, padded to exactly 48 entries
        qualified = [p for p in self.players if p["qualified"]]
        qualified += [{}] * (48 - len(qualified))

        for i in range(0, 48, 4):
            content_layout.addWidget(self._build_player_slot(qualified[i:i + 4]))

        self.root_layout.addWidget(scroll, stretch=1)

    def _build_player_slot(self, player_batch):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(50)

        for player in player_batch:
            player_cont = QWidget()
            player_layout = QVBoxLayout(player_cont)
            player_layout.setContentsMargins(0, 0, 0, 0)
            player_layout.setSpacing(10)

            image = QLabel()
            image.setFixedSize(200, 200)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if player:
                image = HoverImage(Session.get_pixmap("players", player["name"]), size=200)
                info_label = QLabel(f"{player['name']}")
                info_label.setStyleSheet("font-size: 20px; font-weight: bold;")
                info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            else:
                image.setStyleSheet("border: 2px dashed #555; background-color: #333; color: #eee;")
                image.setText("?")
                info_label = QLabel("")

            player_layout.addWidget(image)
            player_layout.addWidget(info_label)
            layout.addWidget(player_cont)

        return row

    def _build_title(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        events = QLabel("Qualified Players")
        events.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events.setStyleSheet("font-size: 64px; font-weight: bold;")

        layout.addWidget(events)

        qualified = QPushButton("Events")
        qualified.setCursor(Qt.CursorShape.PointingHandCursor)
        qualified.clicked.connect(self.app.show_events_view)
        qualified.setStyleSheet(BUTTON_STYLESHEET_A)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(events, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 10, 0)
        right_layout.addStretch()
        right_layout.addWidget(qualified, alignment=Qt.AlignmentFlag.AlignTop)

        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addStretch()

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        return container

    def _view_help(self):
        SoundManager.play("button")

        dialog = QDialog(self)
        dialog.setWindowTitle("Info")
        dialog.setStyleSheet("background: #10194D;")
        dialog.setFixedSize(600, 150)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("Qualified Players")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        title.setStyleSheet("font-weight: bold; font-size: 24px")

        with open(str(ResourcePath.TEXTS / "qualified_help.txt"), "r") as file:
            text_list = file.read().splitlines()

        def _create_label(text):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 14px")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label

        layout.addWidget(title)
        for line in text_list:
            layout.addWidget(_create_label(line))

        dialog.exec()

    @staticmethod
    def preload():
        for player in Session.player_scores or []:
            Session.get_image("players", player["name"])

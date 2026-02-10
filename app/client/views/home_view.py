from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.theme import *
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar

class HomeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        self.my_username = Session.user
        self.my_user_id = Session.user_id

        self._build_static()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0,0,0,0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.content_layout.setContentsMargins(0,0,0,0)

        self.root_layout.addWidget(HeaderBar(self.app))
        self.root_layout.addWidget(self.content_widget)
        self.root_layout.addStretch()
        self.root_layout.addWidget(FooterNav(self.app))

        self._build_sections()
    
    def _build_sections(self):
        if not Session.blocking_state:
            self.content_layout.addWidget(self._build_welcome())
            self.content_layout.addWidget(self._build_home_yap())
        else:
            self.content_layout.addWidget(self._build_blocked())


# -- BUILDERS --

    def _build_welcome(self):
        # user info top row
        tr_cont = QWidget()
        top_row = QHBoxLayout(tr_cont)
        top_row.setContentsMargins(25, 25, 25, 25)

        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.avatar_label = self._build_avatar()
        self.avatar_label.setStyleSheet("border: 5px solid #FFFFFF; border-radius: 5px;")
        self.avatar_label.setFixedSize(250, 250)

        change_btn = QPushButton("Change Avatar")
        change_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        change_btn.clicked.connect(self.update_avatar)

        avatar_layout.addStretch()
        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addWidget(change_btn, alignment= Qt.AlignmentFlag.AlignHCenter)
        avatar_layout.addStretch()

        info = QVBoxLayout()
        info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        info.setSpacing(20)

        label = QLabel(f"Welcome back, {self.my_username}.")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("""
            font-size: 60px; 
            font-weight: bold;
        """)

        subtitle = QLabel(f"User ID: {self.my_user_id}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        subtitle.setStyleSheet("""
            font-size: 14px; 
        """)

        info.addWidget(label)
        info.addWidget(subtitle)

        top_row.addLayout(avatar_layout)
        top_row.addStretch()
        top_row.addLayout(info)
        top_row.addStretch()

        return tr_cont

    def _build_home_yap(self):
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(25,0,25,0)

        main = QLabel("""
Welcome to the first ever Street Fighter 6 Fantasy League! Create leagues with you and up to 5 friends, draft your dream teams of 5 players, and keep an eye out throughout the season and see who comes out on top!

The app works simply. Firstly, head on over to the "League" page where you can create a league or join one using a League ID. Once you're in your league, wait for all your friends to join then the league owner can set the draft order and begin the draft. This fantasy league uses a snake draft; with an order like "Alice, Bob, Charlie", the draft will go "Alice, Bob, Charlie, Charlie, Bob, Alice".

Once the draft is over and you and all your leaguemates have created your dream teams, it's time to wait! You can check out the list of scoring events on the "Events" page, and after each event the scores will be updated for you and your league! You can check out your own standings in the "League" page, or your league's standings in the "Leaderboards" page, where you can view the global player pool and their scores as well as add favourite users for those of you with too many friends for a single league. Thank you for downloading this app, and I hope you win!
               
This app was developed soley by Fararjeh. You can learn more about the developer here: https://fararjeh-fgc.com/.
""")
        main.setWordWrap(True)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addStretch()
        layout.addWidget(main)
        layout.addStretch()

        return cont

    def _build_blocked(self):
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

        return cont


# -- BUTTON METHODS --

    def update_avatar(self):
        """
        Opens a file dialog to select an image and updates the user's avatar.
        """

        # create file dialog manually
        file_dialog = QFileDialog(parent=self)
        file_dialog.setWindowTitle("Select Avatar Image")
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setOption(QFileDialog.Option.ReadOnly, True)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = file_dialog.selectedFiles()[0]
        else:
            return

        # assign avatar
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            Session.auth_base.assign_avatar(file_path)
            Session.avatar_cache.pop(self.my_user_id, None)
            self._refresh_avatar()
            QApplication.restoreOverrideCursor()

            msg = QMessageBox(self)
            msg.setWindowTitle("Change Avatar")
            msg.setText("Avatar updated successfuly!")
            msg.setStyleSheet("background: #10194D;")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()

        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowTitle("Change Avatar")
            msg.setText(f"Avatar updated failed: {e}")
            msg.setStyleSheet("background: #10194D;")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()


# -- HELPERS --

    def _build_avatar(self):
        image = QLabel()
        avatar = QPixmap()

        try:
            avatar.loadFromData(Session.init_avatar(self.my_user_id))
            if avatar.isNull():
                avatar = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        except Exception:
            avatar = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        image.setPixmap(
            avatar.scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        
        return image

    def _refresh_avatar(self):
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(Session.init_avatar(self.my_user_id))
            if pixmap.isNull():
                pixmap = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        except Exception as e:
            pixmap = QPixmap(str(ResourcePath.AVATAR / "placeholder.png"))

        self.avatar_label.setPixmap(
            pixmap.scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

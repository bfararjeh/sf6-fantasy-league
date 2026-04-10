from copy import deepcopy

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.image_cache import ImageCache
from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager
from app.client.theme import *
from app.client.widgets.misc import _build_empty_label, fit_text_to_width

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

        self.root_layout.addWidget(self.content_widget)

        self._build_sections()
    
    def _build_sections(self):
        if not Session.blocking_state:
            self.content_layout.addWidget(self._build_welcome())
            self.content_layout.addStretch()
            self.content_layout.addWidget(self._build_home_yap())
            self.content_layout.addStretch()
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

        label = QLabel("")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("""
            font-weight: bold;
        """)
        fit_text_to_width(label, f"Welcome back, {self.my_username}.", 850, 2, 60)

        subtitle = QLabel(f"User ID: {self.my_user_id}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        subtitle.setStyleSheet("""
            font-size: 14px; 
        """)

        info.addWidget(label)
        info.addWidget(subtitle)

        top_row.addLayout(avatar_layout)
        top_row.addLayout(info, stretch=1)

        return tr_cont

    def _build_home_yap(self):
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(75,0,75,0)

        main = QLabel()
        with open(str(ResourcePath.TEXTS / "home_yap.txt"), "r") as file:
            text = file.read()
        main.setText(text)
        main.setWordWrap(True)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(main)
        layout.addStretch()

        return cont

    def _build_blocked(self):
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(25,0,25,0)

        layout.addStretch()
        layout.addWidget(_build_empty_label())
        layout.addStretch()

        return cont


# -- BUTTON METHODS --

    def update_avatar(self):
        """
        Opens a file dialog to select an image and updates the user's avatar.
        """

        if Session.blocking_state:
            return
        
        SoundManager.play("prompt")

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
            ImageCache.invalidate("avatars", str(self.my_user_id))
            self._refresh_avatar()
            QApplication.restoreOverrideCursor()

            msg = QMessageBox(self)
            msg.setWindowTitle("Change Avatar")
            msg.setText("Avatar updated successfuly!")
            msg.setStyleSheet("background: #10194D;")
            msg.setIcon(QMessageBox.Icon.NoIcon)
            SoundManager.play("success")
            msg.exec()

        except Exception as e:
            QApplication.restoreOverrideCursor()
            msg = QMessageBox(self)
            msg.setWindowTitle("Change Avatar")
            msg.setText(f"Avatar updated failed: {e}")
            msg.setStyleSheet("background: #10194D;")
            msg.setIcon(QMessageBox.Icon.NoIcon)
            SoundManager.play("error")
            msg.exec()


# -- HELPERS --

    def _build_avatar(self):
        image = QLabel()
        image.setPixmap(
            Session.get_pixmap("avatars", self.my_user_id).scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        return image

    def _refresh_avatar(self):
        self.avatar_label.setPixmap(
            Session.get_pixmap("avatars", self.my_user_id).scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def _view_help(self):
        SoundManager.play("button")

        dialog = QDialog(self)
        dialog.setWindowTitle("Info")
        dialog.setStyleSheet("background: #10194D;")
        dialog.setFixedSize(600, 250)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("Home")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        title.setStyleSheet("font-weight: bold; font-size: 24px")

        with open(str(ResourcePath.TEXTS / "home_help.txt"), "r") as file:
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

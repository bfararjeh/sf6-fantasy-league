from pathlib import Path
import sys

from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton, 
    QFileDialog, 
    QMessageBox
)

from PyQt6.QtCore import Qt

from PyQt6.QtGui import QPixmap

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

from app.client.controllers.session import Session

from app.client.theme import *


class HomeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.AVATAR_IMG_PATH = Path(self._resource_path("app/client/assets/avatars"))
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

        self._build_dynamic()
    
    def _build_dynamic(self):
        self.content_layout.addWidget(self._build_welcome())


# -- BUILDERS --

    def _build_welcome(self):
        # user info top row
        tr_cont = QWidget()
        top_row = QHBoxLayout(tr_cont)
        top_row.setContentsMargins(25, 25, 25, 25)

        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.avatar_label = self._build_avatar()
        self.avatar_label.setStyleSheet("border: 5px solid #FFFFFF;")
        self.avatar_label.setFixedSize(250, 250)

        change_btn = QPushButton("Change Avatar")
        change_btn.setStyleSheet(BUTTON_STYLESHEET)
        change_btn.clicked.connect(self.update_avatar)

        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addWidget(change_btn, alignment= Qt.AlignmentFlag.AlignHCenter)

        info = QVBoxLayout()
        info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        info.setSpacing(20)

        label = QLabel(f"Welcome back, {self.my_username}.")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("""
            font-size: 54px; 
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


# -- BUTTON METHODS --

    def update_avatar(self):
        """
        Opens a file dialog to select an image and updates the user's avatar.
        """

        # ----------------------
        # Create file dialog manually to apply stylesheet
        # ----------------------
        file_dialog = QFileDialog(parent=self)
        file_dialog.setWindowTitle("Select Avatar Image")
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        # Use non-native dialog to allow styling
        file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        file_dialog.setOption(QFileDialog.Option.ReadOnly, True)

        # ----------------------
        # Apply your stylesheet
        # ----------------------
        file_dialog.setStyleSheet(FILE_DIALOG_STYLESHEET)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = file_dialog.selectedFiles()[0]
        else:
            return

        try:
            Session.auth_base.assign_avatar(file_path)
            Session.avatar_cache.pop(self.my_user_id, None)
            self._refresh_avatar()

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

        try:
            avatar = QPixmap()
            avatar.loadFromData(Session.init_avatar(self.my_user_id))
            if avatar.isNull():
                avatar = QPixmap(str(self.AVATAR_IMG_PATH / "placeholder.png"))

        except Exception:
            avatar = QPixmap(str(self.AVATAR_IMG_PATH / "placeholder.png"))

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
                pixmap = QPixmap(str(self.AVATAR_IMG_PATH / "placeholder.png"))

        except Exception as e:
            pixmap = QPixmap(str(self.AVATAR_IMG_PATH / "placeholder.png"))

        self.avatar_label.setPixmap(
            pixmap.scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def _resource_path(self, relative_path: str) -> str:
        if hasattr(sys, "_MEIPASS"):
            return str(Path(sys._MEIPASS) / relative_path)
        return str(Path(relative_path).resolve())
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer

from time import sleep

from app.services.auth_service import AuthService
from app.client.session import Session


class LoginView(QWidget):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout()

        # title
        title = QLabel("Fantasy Street Fighter 6")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        # footer
        footer = QLabel("© 2026 Fararjeh, All rights reserved.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #888888;
            }
            """
        )

        # email & pass
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(30)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(30)

        # login button
        self.submit_button = QPushButton("Login")
        self.submit_button.setFixedHeight(40)
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self.attempt_login)
        self.submit_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #2d7df6;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1f6ae1;
            }
            QPushButton:pressed {
                background-color: #1a5bc4;
            }
            """
        )

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
            """
        )

        # form container for width control
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.submit_button)
        form_layout.addWidget(self.status_label)

        form_container = QWidget()
        form_container.setLayout(form_layout)
        form_container.setFixedWidth(320)

        # content container for centering
        content_container = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(20)

        content_layout.addWidget(title)
        content_layout.addWidget(form_container)

        content_container.setLayout(content_layout)

        # assemble
        root_layout.addStretch()
        root_layout.addWidget(content_container)
        root_layout.addStretch()
        root_layout.addWidget(footer)

        self.setLayout(root_layout)
    
    def attempt_login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        
        self.status_label.setText("Logging in...")
        self.status_label.setStyleSheet("color: #555555;")
        QApplication.processEvents()

        try:
            base = AuthService.login(email, password)
            Session.auth_base = base
            Session.user = base.get_my_username()

            self.status_label.setText(f"Login successful! Welcome back {Session.user}.")
            self.status_label.setStyleSheet("color: #2e7d32;")

            if self.app:
                QTimer.singleShot(2000, self.app.show_home_view)

        except Exception as e:
            self.status_label.setText(f"Login failed: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")
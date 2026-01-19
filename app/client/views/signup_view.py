from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QApplication,
    QToolButton
)
from PyQt6.QtCore import Qt

from PyQt6.QtGui import QIcon

from app.services.signup_service import SignupService


class SignupView(QWidget):
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

        # help button
        help_label = QLabel()
        help_label.setText("Username must be 2-16 characters, letters, numbers, underscores, and apostrophes only.\n\n"
            "Password must be at least 8 characters long.")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setWordWrap(True)
        help_label.setFixedHeight(65)
        help_label.setStyleSheet("color: #333")

        # email pass & username
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Username")
        self.name_input.setFixedHeight(30)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(30)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(30)

        self.password_verify_input = QLineEdit()
        self.password_verify_input.setPlaceholderText("Re-enter password")
        self.password_verify_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_verify_input.setFixedHeight(30)

        # back to login page
        return_to_login = QPushButton("Return to login page")
        return_to_login.setCursor(Qt.CursorShape.PointingHandCursor)
        return_to_login.setFlat(True)
        return_to_login.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #007acc;
                font-size: 12px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        return_to_login.clicked.connect(self.app.show_login_view)

        # signup button
        self.submit_button = QPushButton("Sign Up")
        self.submit_button.setFixedHeight(40)
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self.attempt_signup)
        self.submit_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #4200ff;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #642bff;
            }
            QPushButton:pressed {
                background-color: #3900d5;
            }
            """
        )

        # status label
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
        form_layout.addWidget(help_label)
        form_layout.addSpacing(5)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.password_verify_input)
        form_layout.addWidget(return_to_login)
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

    def _set_inputs_enabled(self, enabled: bool):
        self.name_input.setEnabled(enabled)
        self.email_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.password_verify_input.setEnabled(enabled)
        self.submit_button.setEnabled(enabled)
    
    def attempt_signup(self):
        '''
        Attempts to create a new user with provided credentials
        '''
        email = self.email_input.text()
        password = self.password_input.text()
        username = self.name_input.text()

        if password != self.password_verify_input.text():
            self.status_label.setText(f"Passwords must match!")
            self.status_label.setStyleSheet("color: #cc0000;")
            return

        self._set_inputs_enabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        self.status_label.setText("Creating user...")
        self.status_label.setStyleSheet("color: #555555;")
        QApplication.processEvents()

        signup = SignupService()
        try:
            success = signup.signup(email=email, password=password, manager_name=username)
            if success == True:
                QApplication.restoreOverrideCursor()
                self.status_label.setText(f"Signup successful! You may return to the login page.")
                self.status_label.setStyleSheet("color: #2e7d32;")
            else:
                raise Exception("Unable to create user.")

        except Exception as e:
            self.status_label.setText(f"Login failed: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")
            self._set_inputs_enabled(True)
            QApplication.restoreOverrideCursor()
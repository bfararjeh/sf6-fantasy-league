from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.session import Session
from app.services.auth_service import AuthService
from app.services.auth_store import AuthStore

class LoginView(QWidget):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout()

        # title
        title = QLabel("Fantasy Street Fighter 6")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
        """)

        # footer
        footer = QLabel("© 2026 Fararjeh, All rights reserved.")
        footer.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)

        # email & pass
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(30)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(30)

        self.email_input.returnPressed.connect(self._attempt_login)
        self.password_input.returnPressed.connect(self._attempt_login)

        # back to signup page
        return_to_login = QPushButton("New user?")
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
        return_to_login.clicked.connect(self.app.show_signup_view)

        # login button
        self.submit_button = QPushButton("Login")
        self.submit_button.setFixedHeight(40)
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self._attempt_login)
        self.submit_button.setStyleSheet("""
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
        """)

        # status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #FFD700;
            }
        """)

        # form container for width control
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        form_layout.addWidget(title)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(return_to_login)
        form_layout.addWidget(self.submit_button)
        form_layout.addWidget(self.status_label)

        form_container = QWidget()
        form_container.setFixedWidth(350)
        form_container.setLayout(form_layout)

        # assemble
        root_layout.addStretch()
        root_layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        root_layout.addStretch()
        root_layout.addWidget(footer)

        self.setLayout(root_layout)

    def _toggle_inputs(self, enabled: bool):
        self.email_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.submit_button.setEnabled(enabled)
    
    def _attempt_login(self):
        '''
        Attempts to login a user with the provided email and password.
        Initialises the Session class as well as storing the access & refresh
        token for subsequent logins.
        '''
        email = self.email_input.text()
        password = self.password_input.text()

        if not email or not password:
            self.status_label.setText(f"Please enter your login details.")
            self.status_label.setStyleSheet("color: #FFD700;")
            return

        self._toggle_inputs(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        self.status_label.setText("Logging in...")
        self.status_label.setStyleSheet("color: #555555;")
        QApplication.processEvents()

        try:
            base = AuthService.login(email, password)
            Session.auth_base = base
            Session.user = base.get_my_username()
            Session.init_services()
            Session.init_system_state()

            AuthStore.save({
                "access_token": base.access_token,
                "refresh_token": base.refresh_token,
            })

            QApplication.restoreOverrideCursor()
            self.status_label.setText(f"Login successful! Welcome back {Session.user}.")
            self.status_label.setStyleSheet("color: #4ade00;")

            if self.app:
                QTimer.singleShot(2000, self._login_success)

        except Exception as e:
            self.status_label.setText(f"Login failed: {e}")
            self.status_label.setStyleSheet("color: #FFD700;")
        
        finally:
            self._toggle_inputs(True)
            QApplication.restoreOverrideCursor()

    def _login_success(self):
        self.status_label.setText("")
        self.email_input.setText("")
        self.password_input.setText("")
        self._toggle_inputs(True)

        self.app.show_home_view()

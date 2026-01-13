from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt
from app.client.session import Session
from app.client.views.login_view import LoginView
# from app.client.views.home_view import HomeView


class FantasyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fantasy Street Fighter 6")
        self.resize(800, 600)

        # login view is default
        self.login_view = LoginView(app=self)
        self.setCentralWidget(self.login_view)

    def show_home_view(self):
        from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

        home = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Home View Placeholder {Session.user}"))
        home.setLayout(layout)

        self.setCentralWidget(home)
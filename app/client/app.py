import webbrowser

from PyQt6.QtWidgets import QMainWindow, QApplication, QStackedWidget

from PyQt6.QtGui import QKeySequence, QShortcut

from PyQt6.QtCore import Qt

from app.services.auth_store import AuthStore
from app.services.app_store import AppStore
from app.services.auth_service import AuthService

from app.client.widgets.blue_screen import BlueScreen

from app.client.controllers.session import Session

from app.client.views.login_view import LoginView
from app.client.views.signup_view import SignupView
from app.client.views.home_view import HomeView
from app.client.views.league_view import LeagueView
from app.client.views.team_view import TeamView
from app.client.views.player_view import PlayerView
from app.client.views.leaderboard_view import LeaderboardView

class FantasyApp(QMainWindow):
    '''
    Main app file for the application. Has functions for displaying all views.

    Also responsible for restoring user sessions on launch, otherwise 
    displaying the login view.
    '''
    def __init__(self):
        super().__init__()

        # instantiating blue screen, just in case ;)
        self.blue_screen = BlueScreen(self)

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close)

        self.setWindowTitle("SF6 Fantasy League")
        self.setFixedSize(1000, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # view placeholders
        self.login_view = None
        self.signup_view = None
        self.home_view = None
        self.league_view = None
        self.team_view = None
        self.player_view = None
        self.leaderboard_view = None

        if self._try_restore_session():
            self.show_home_view()
        else:
            self.show_login_view()

    def _try_restore_session(self) -> bool:
        data = AuthStore.load()
        if not data:
            return False

        try:
            base = AuthService.login_with_token(data)
            Session.auth_base = base
            Session.init_services()
            Session.init_system_state()
            return True
        
        except Exception as e:
            # clears cached session if failed to login
            AuthStore.clear()
            AppStore.clear()
            return False
    

    def show_login_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.login_view is None:
                self.login_view = LoginView(app=self)
                self.stack.addWidget(self.login_view)
            self.stack.setCurrentWidget(self.login_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_signup_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.signup_view is None:
                self.signup_view = SignupView(app=self)
                self.stack.addWidget(self.signup_view)
            self.stack.setCurrentWidget(self.signup_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_home_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.home_view is None:
                self.home_view = HomeView(app=self)
                self.stack.addWidget(self.home_view)
            self.stack.setCurrentWidget(self.home_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_league_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.league_view is None:
                self.league_view = LeagueView(app=self)
                self.stack.addWidget(self.league_view)
            self.stack.setCurrentWidget(self.league_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_team_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.team_view is None:
                self.team_view = TeamView(app=self)
                self.stack.addWidget(self.team_view)
            self.stack.setCurrentWidget(self.team_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_players_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.player_view is None:
                self.player_view = PlayerView(app=self)
                self.stack.addWidget(self.player_view)
            self.stack.setCurrentWidget(self.player_view)
        finally:
            QApplication.restoreOverrideCursor()

    def show_leaderboards_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.leaderboard_view is None:
                self.leaderboard_view = LeaderboardView(app=self)
                self.stack.addWidget(self.leaderboard_view)
            self.stack.setCurrentWidget(self.leaderboard_view)
        finally:
            QApplication.restoreOverrideCursor()


    def open_help(self):
        webbrowser.open(
            "https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs"
        )

    def logout(self):
        Session.reset()
        AuthStore.clear()
        AppStore.clear()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # view placeholders
        self.login_view = None
        self.signup_view = None
        self.home_view = None
        self.league_view = None
        self.team_view = None
        self.player_view = None
        self.leaderboard_view = None

        self.show_login_view()
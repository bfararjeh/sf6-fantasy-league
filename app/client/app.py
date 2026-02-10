import webbrowser

from PyQt6.QtWidgets import QMainWindow, QApplication, QStackedWidget

from PyQt6.QtGui import QKeySequence, QShortcut, QPalette

from PyQt6.QtCore import Qt, QTimer

from app.client.views.global_view import GlobalView
from app.services.auth_store import AuthStore
from app.services.auth_service import AuthService

from app.client.widgets.blue_screen import BlueScreen

from app.client.controllers.session import Session

from app.client.views.login_view import LoginView
from app.client.views.signup_view import SignupView
from app.client.views.home_view import HomeView
from app.client.views.league_view import LeagueView
from app.client.views.leaderboard_view import LeaderboardView
from app.client.views.player_view import PlayerView

class FantasyApp(QMainWindow):
    '''
    Main app file for the application. Has functions for displaying all views.

    Also responsible for restoring user sessions on launch, otherwise 
    displaying the login view.
    '''
    def __init__(self):
        super().__init__()
        try:

            # instantiating blue screen, just in case ;)
            self.blue_screen = BlueScreen(self)

            close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
            close_shortcut.activated.connect(self.close)

            self.setWindowTitle("SF6 Fantasy League")
            self.setFixedSize(1200, 800)

            self.stack = QStackedWidget()
            self.setCentralWidget(self.stack)

            # view placeholders
            self.login_view = None
            self.signup_view = None

            self.home_view = None
            self.league_view = None
            self.leaderboard_view = None
            self.players_view = None
            self.globals_view = None
            self.events_view = None
            self.trades_view = None

            self.refresh_timer = QTimer()
            self.refresh_timer.setInterval(60 * 1000)
            self.refresh_timer.timeout.connect(self._refresh_current_view)
            self.refresh_timer.start()

            if self._try_restore_session():
                self.show_home_view()
            else:
                self.show_login_view()
        except Exception as e:
            print(e)

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
            return False
    

# -- LOGIN/SIGNUP VIEWS --
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


# -- MAIN VIEWS --
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
            self.refresh_timer.stop()
            self.refresh_timer.start()
        finally:
            QApplication.restoreOverrideCursor()

    def show_leaderboards_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.leaderboard_view is None:
                self.leaderboard_view = LeaderboardView(app=self)
                self.stack.addWidget(self.leaderboard_view)
            self.stack.setCurrentWidget(self.leaderboard_view)
            self.refresh_timer.stop()
            self.refresh_timer.start()
        finally:
            QApplication.restoreOverrideCursor()

    def show_players_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.players_view is None:
                self.players_view = PlayerView(app=self)
                self.stack.addWidget(self.players_view)
            self.stack.setCurrentWidget(self.players_view)
            self.refresh_timer.stop()
            self.refresh_timer.start()
        finally:
            QApplication.restoreOverrideCursor()

    def show_globals_view(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if self.globals_view is None:
                self.globals_view = GlobalView(app=self)
                self.stack.addWidget(self.globals_view)
            self.stack.setCurrentWidget(self.globals_view)
            self.refresh_timer.stop()
            self.refresh_timer.start()
        finally:
            QApplication.restoreOverrideCursor()

    def show_events_view(self):
        print("Events view requested.")

    def show_trades_view(self):
        print("Trades view requested.")

# -- HEADER HELPERS --
    def open_help(self):
        webbrowser.open(
            "https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs"
        )

    def logout(self):
        # stop refresh timer
        self.refresh_timer.stop()

        # reset session
        Session.reset()
        AuthStore.clear()

        # safely remove old views
        for view in [
            self.league_view, 
            self.home_view, 
            self.leaderboard_view, 
            self.players_view, 
            self.globals_view,
            self.events_view, 
            self.trades_view
            ]:
            if view is not None:
                view.hide()
                view.setParent(None)

        # reset references
        self.home_view = None
        self.league_view = None
        self.leaderboard_view = None
        self.players_view = None
        self.globals_view = None
        self.events_view = None
        self.trades_view = None

        self.show_login_view()
    
# -- AUTO REFRESH CONTROL --
    def _refresh_current_view(self):
        try:
            current_view = self.stack.currentWidget()
            current_view._refresh()
        except Exception as e:
            print(e)
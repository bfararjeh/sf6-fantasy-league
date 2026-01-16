from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from app.client.views.league_view import LeagueView
from app.services.session_store import SessionStore
from app.services.auth_service import AuthService
from app.client.session import Session
from app.client.views.login_view import LoginView
from app.client.views.home_view import HomeView


class FantasyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SF6 Fantasy League")
        self.resize(1000, 800)

        if self._try_restore_session():
            self.show_home_view()
        else:
            self.show_login_view()

    def _try_restore_session(self) -> bool:
        data = SessionStore.load()
        if not data:
            return False

        try:
            base = AuthService.login_with_token(data)

            Session.auth_base = base
            Session.user = base.get_my_username()
            Session.init_services()

            return True
        except Exception as e:
            print(e)
            SessionStore.clear()
            return False
    
    def show_login_view(self):
        self.login_view = LoginView(app=self)
        self.setCentralWidget(self.login_view)

    def show_home_view(self):
        self.home_view = HomeView(app=self)
        self.setCentralWidget(self.home_view)

    def show_league_view(self):
        self.league_view = LeagueView(app=self)
        self.setCentralWidget(self.league_view)

    def show_team_view(self):
        print("Team view requested")

    def show_players_view(self):
        print("Players view requested")

    def show_leaderboards_view(self):
        print("Leaderboards view requested")

    def open_help(self):
        import webbrowser
        webbrowser.open("https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs")
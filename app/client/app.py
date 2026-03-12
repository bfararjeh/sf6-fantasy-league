import webbrowser

from PyQt6.QtWidgets import QMainWindow, QApplication, QStackedWidget

from PyQt6.QtGui import QKeySequence, QShortcut


from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QComboBox,
    QAbstractSpinBox
)
from PyQt6.QtCore import QTimer

from app.client.views.global_view import GlobalView
from app.client.views.loading_view import LoadingView
from app.client.views.trade_view import TradeView
from app.client.widgets.footer_nav import FooterNav
from app.client.widgets.header_bar import HeaderBar
from app.services.auth_store import AuthStore
from app.services.auth_service import AuthService

from app.client.widgets.blue_screen import BlueScreen
from app.client.widgets.view_loader import load_view

from app.client.controllers.session import Session
from app.client.views.login_view import LoginView
from app.client.views.signup_view import SignupView
from app.client.views.home_view import HomeView
from app.client.views.league_view import LeagueView
from app.client.views.leaderboard_view import LeaderboardView
from app.client.views.player_view import PlayerView
from app.client.views.event_view import EventView
from app.client.views.qualified_view import QualifiedView

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QStackedWidget
)


class FantasyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.instance().installEventFilter(self)
        self._active_threads = []
        self.blue_screen = BlueScreen(self)

        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close)
        self.setWindowTitle("Fantasy SF6")
        self.setFixedSize(1200, 800)

        self.header = HeaderBar(self)
        self.footer = FooterNav(self)
        self.stack = QStackedWidget()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.header)
        central_layout.addWidget(self.stack, stretch=1)
        central_layout.addWidget(self.footer)
        self.setCentralWidget(central)

        self.loading_view = None
        self.login_view = None
        self.signup_view = None
        self.home_view = None
        self.league_view = None
        self.leaderboard_view = None
        self.players_view = None
        self.globals_view = None
        self.events_view = None
        self.qualified_view = None
        self.trades_view = None

        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)

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
            Session.init_system_state()
            Session.init_services()
            return True
        except Exception:
            AuthStore.clear()
            return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            focused = QApplication.focusWidget()
            if focused and not isinstance(
                obj, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QAbstractSpinBox)
            ):
                focused.clearFocus()
        return super().eventFilter(obj, event)


# -- LOGIN/SIGNUP VIEWS --

    def show_login_view(self):
        self.header.setVisible(False)
        self.footer.setVisible(False)
        self.header.refresh_button.setVisible(False)
        if self.login_view is None:
            self.login_view = LoginView(app=self)
            self.stack.addWidget(self.login_view)
        self.stack.setCurrentWidget(self.login_view)

    def show_signup_view(self):
        self.header.setVisible(False)
        self.footer.setVisible(False)
        self.header.refresh_button.setVisible(False)
        if self.signup_view is None:
            self.signup_view = SignupView(app=self)
            self.stack.addWidget(self.signup_view)
        self.stack.setCurrentWidget(self.signup_view)


# -- MAIN VIEWS --

    def show_home_view(self):
        if not Session._on_block:
            Session._on_block = lambda: self.footer.refresh()
            self.footer.refresh()
            self.header.refresh()

        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()

        if self.home_view is None:
            self.home_view = HomeView(app=self)
            self.stack.addWidget(self.home_view)
        if self.loading_view is None:
            self.loading_view = LoadingView(app=self)
            self.stack.addWidget(self.loading_view)
        self.stack.setCurrentWidget(self.home_view)


# -- DYNAMIC VIEWS --

    def show_league_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(True)
        if self.league_view is not None:
            self.stack.setCurrentWidget(self.league_view)
            self.connect_refresh(self.league_view._refresh)
            self._start_refresh_timer()
            return

        blocked = False

        def _fetch():
            nonlocal blocked
            Session.init_system_state()
            if Session.blocking_state:
                blocked = True
                return
            Session.init_league_data(force=1)
            Session.init_player_scores()

        def _done():
            if blocked:
                self.footer.refresh()
                return
            self.league_view = LeagueView(app=self)
            self.stack.addWidget(self.league_view)
            self.connect_refresh(self.league_view._refresh)
            self._start_refresh_timer()

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)

    def show_leaderboards_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(True)
        if self.leaderboard_view is not None:
            self.stack.setCurrentWidget(self.leaderboard_view)
            self.connect_refresh(self.leaderboard_view._refresh)
            self._start_refresh_timer()
            return

        blocked = False

        def _fetch():
            nonlocal blocked
            Session.init_system_state()
            if Session.blocking_state:
                blocked = True
                return
            Session.init_leaderboards(force=1)

        def _done():
            if blocked:
                self.footer.refresh()
                return
            self.leaderboard_view = LeaderboardView(app=self)
            self.stack.addWidget(self.leaderboard_view)
            self.connect_refresh(self.leaderboard_view._refresh)
            self._start_refresh_timer()

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)


# -- STATIC VIEWS --

    def show_players_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()
        if self.players_view is not None:
            self.stack.setCurrentWidget(self.players_view)
            return

        def _fetch():
            Session.init_player_scores()
            PlayerView.preload()

        def _done():
            self.players_view = PlayerView(app=self)
            self.stack.addWidget(self.players_view)

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)

    def show_globals_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()
        if self.globals_view is not None:
            self.stack.setCurrentWidget(self.globals_view)
            return

        def _fetch():
            Session.init_global_stats()
            GlobalView.preload()

        def _done():
            self.globals_view = GlobalView(app=self)
            self.stack.addWidget(self.globals_view)

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)

    def show_events_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()
        if self.events_view is not None:
            self.stack.setCurrentWidget(self.events_view)
            return

        def _fetch():
            Session.init_event_data()
            Session.init_league_data()

        def _done():
            self.events_view = EventView(app=self)
            self.stack.addWidget(self.events_view)

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)

    def show_qualified_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()
        if self.qualified_view is not None:
            self.stack.setCurrentWidget(self.qualified_view)
            return

        def _fetch():
            Session.init_qualified_data()

        def _done():
            self.qualified_view = QualifiedView(app=self)
            self.stack.addWidget(self.qualified_view)

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)

    def show_trades_view(self):
        self.header.setVisible(True)
        self.footer.setVisible(True)
        self.header.refresh_button.setVisible(False)
        self._refresh_timer.stop()
        if self.trades_view is not None:
            self.stack.setCurrentWidget(self.trades_view)
            return

        def _fetch():
            pass

        def _done():
            self.trades_view = TradeView(app=self)
            self.stack.addWidget(self.trades_view)

        load_view(self.stack, self.loading_view, _fetch, _done, self._active_threads)


# -- HEADER --

    def open_help(self):
        webbrowser.open(
            "https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs"
        )

    def logout(self):
        Session.reset()
        AuthStore.clear()
        self._refresh_timer.stop()

        for view in [
            self.loading_view, self.league_view, self.home_view,
            self.leaderboard_view, self.players_view, self.globals_view,
            self.events_view, self.trades_view, self.login_view, self.signup_view,
            self.qualified_view
        ]:
            if view is not None:
                view.hide()
                view.setParent(None)

        self.loading_view = self.home_view = self.league_view = None
        self.leaderboard_view = self.players_view = self.globals_view = None
        self.events_view = self.trades_view = self.qualified_view = None
        self.login_view = self.signup_view = None

        self.show_login_view()


# -- REFRESH --

    def connect_refresh(self, callback):
        try:
            self.header.refresh_button.refresh_requested.disconnect()
        except Exception:
            pass
        self.header.refresh_button.refresh_requested.connect(
            lambda: self._do_refresh(callback, manual=True)
        )

    def _do_refresh(self, callback, manual=False):
        view = self.stack.currentWidget()
        try:
            if manual:
                view._set_status("Refreshing...", code=0)
            view.setEnabled(False)
            self.header.setEnabled(False)
            QApplication.processEvents()
            callback()
            if manual:
                view._set_status("Refreshed!", code=1)
        except Exception as e:
            if manual:
                view._set_status(f"Refresh failed: {e}", code=2)
        finally:
            view.setEnabled(True)
            self.header.setEnabled(True)

    def _auto_refresh(self):
        current = self.stack.currentWidget()
        if current in (self.league_view, self.leaderboard_view):
            if hasattr(current, '_refresh'):
                self._do_refresh(current._refresh)
        self._update_refresh_interval()

    def _update_refresh_interval(self):
        interval = Session.get_refresh_interval()
        if self._refresh_timer.interval() != interval:
            self._refresh_timer.setInterval(interval)

    def _start_refresh_timer(self):
        self._update_refresh_interval()
        self._refresh_timer.start()

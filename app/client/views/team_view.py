from PyQt6.QtWidgets import (
    QWidget, 
    QLabel, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLineEdit, 
    QGroupBox,
    QFrame,
    QSizePolicy,
    QScrollArea
)

from PyQt6.QtCore import Qt

from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async

from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav

class LeagueView(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app

        # root layout: defined here to use in other private methods
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        # clears then builds ui
        Session.init_aesthetics()
        self._refresh_view()


    def _build_main(self):
        pass

    def _build_my_info(self):
        pass
    
    def _build_player_list(self):
        pass


    def _refresh_view(self):
        self._clear_layout(self.layout())
        Session.init_aesthetics()
        self._build_main()

    def _clear_layout(self, layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #7a7a7a;")
        separator.setFixedHeight(2)
        separator.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        return separator

'''    def _set_status(self, msg, status_type):
        self.status_label.setText(msg)

        if status_type == "s":
            color = "#2e7d32"
        elif status_type == "e":
            color = "#cc0000"
        else:
            color = "#333333"

        self.status_label.setStyleSheet(f"color: {color};")'''
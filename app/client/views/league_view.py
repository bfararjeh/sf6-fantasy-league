from PyQt6.QtWidgets import (
    QWidget, 
    QLabel, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLineEdit, 
    QGroupBox
)

from PyQt6.QtCore import Qt

from app.client.session import Session

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
        self._refresh_view()

    def _build_ui(self):
        # header
        self.root_layout.addWidget(HeaderBar(self.app))

        # main content
        content_widget = QWidget()

        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        # grabbing league aesthetics
        league_name = Session.current_league_name or "None"
        league_id = Session.current_league_id or "N/A"
        league_forfeit = Session.league_forfeit or None
        is_owner = Session.is_league_owner or False

        # league owner, name, and id
        league_info_container = QWidget()
        league_info_layout = QVBoxLayout(league_info_container)
        league_info_layout.setSpacing(10)
        league_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.league_owner = QLabel("Owner")
        self.league_owner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_owner.setStyleSheet("font-size: 20px; font-weight: bold; color: #7d130b;")

        self.league_name_label = QLabel(f"Current League: {league_name}")
        self.league_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")

        self.league_id_label = QLabel(f"ID: {league_id}")
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setStyleSheet("font-size: 14px; color: #222;")

        if is_owner == True:
            league_info_layout.addWidget(self.league_owner)
        league_info_layout.addWidget(self.league_name_label)
        league_info_layout.addWidget(self.league_id_label)

        content_layout.addWidget(league_info_container)

        # forfeit label only when in league
        self.forfeit_label = QLabel(f"Forfeit: {league_forfeit}")
        self.forfeit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.forfeit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")

        if league_forfeit != None:
            content_layout.addWidget(self.forfeit_label)

        # create league
        self.create_input = QLineEdit()
        self.create_input.setPlaceholderText("League Name")

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_league)

        create_layout = QHBoxLayout()
        create_layout.addWidget(self.create_input)
        create_layout.addWidget(create_btn)

        create_group = QGroupBox("Create League")
        create_group.setLayout(create_layout)

        # join league
        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")

        join_btn = QPushButton("Join")
        join_btn.clicked.connect(self.join_league)

        join_layout = QHBoxLayout()
        join_layout.addWidget(self.join_input)
        join_layout.addWidget(join_btn)

        join_group = QGroupBox("Join League")
        join_group.setLayout(join_layout)

        # leave league
        leave_btn = QPushButton("Leave League")
        leave_btn.clicked.connect(self.leave_league)

        # draft order
        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Usernames")

        draft_order_btn = QPushButton("Assign Draft Order")
        draft_order_btn.clicked.connect(self.assign_draft_order)

        draft_btn = QPushButton("Submit")
        draft_btn.clicked.connect(self.assign_draft_order)

        draft_layout = QHBoxLayout()
        draft_layout.addWidget(self.draft_input)
        draft_layout.addWidget(draft_btn)

        draft_group = QGroupBox("Assign Draft Order")
        draft_group.setLayout(draft_layout)

        # begin draft
        begin_draft_btn = QPushButton("Begin Draft")
        begin_draft_btn.clicked.connect(self.begin_draft)

        # forfeit setter
        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Forfeit")

        forfeit_btn = QPushButton("Submit")
        forfeit_btn.clicked.connect(self.set_forfeit)

        forfeit_layout = QHBoxLayout()
        forfeit_layout.addWidget(self.forfeit_input)
        forfeit_layout.addWidget(forfeit_btn)

        forfeit_group = QGroupBox("Set Forfeit")
        forfeit_group.setLayout(forfeit_layout)

        # defining widgets to show owner
        self.owner_controls = QWidget()
        owner_layout = QVBoxLayout(self.owner_controls)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(10)

        owner_layout.addWidget(draft_group)
        owner_layout.addWidget(begin_draft_btn)
        owner_layout.addWidget(forfeit_group)

        # defining widgets to show to those with no league
        self.leagueless_controls = QWidget()
        leagueless_layout = QVBoxLayout(self.leagueless_controls)
        leagueless_layout.setContentsMargins(0, 0, 0, 0)
        leagueless_layout.setSpacing(10)

        leagueless_layout.addWidget(create_group)
        leagueless_layout.addWidget(join_group)

        # defining widgets to show those in a league
        self.in_league_controls = QWidget()
        in_league_layout = QVBoxLayout(self.in_league_controls)
        in_league_layout.setContentsMargins(0, 0, 0, 0)
        in_league_layout.setSpacing(10)

        in_league_layout.addWidget(leave_btn)

        # status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
        """)

        # add the owner_controls container to main content layout
        content_layout.addWidget(self.owner_controls)
        content_layout.addWidget(self.leagueless_controls)
        content_layout.addWidget(self.in_league_controls)
        content_layout.addWidget(self.status_label)

        self.owner_controls.setVisible(Session.is_league_owner)

        if Session.current_league_id == None:
            self.leagueless_controls.setVisible(True)
            self.in_league_controls.setVisible(False)
        else:
            self.leagueless_controls.setVisible(False)
            self.in_league_controls.setVisible(True)


        self.root_layout.addWidget(content_widget, stretch=1)

        self.root_layout.addWidget(FooterNav(self.app))

    # methods wired up to league service
    def create_league(self):
        name = self.create_input.text().strip()

        if not name:
            self.status_label.setText("Please enter a league name.")
            return

        try:
            success = Session.league_service.create_then_join_league(name)
            if success:
                Session.init_aesthetics()
                self._refresh_view()

                self.status_label.setText("League created successfully!")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to create league: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def join_league(self):
        league_id = self.join_input.text().strip()

        if not league_id:
            self.status_label.setText("Please enter a league ID.")
            return
        
        try:
            success = Session.league_service.join_league(league_id)
            if success:
                Session.init_aesthetics()
                self._refresh_view()

                self.status_label.setText("League joined successfully!")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to join league: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def leave_league(self):
        try:
            success = Session.league_service.leave_league()
            if success:
                Session.init_aesthetics()  
                self._refresh_view()

                self.status_label.setText("You have left the league successfully.")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to leave league: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def assign_draft_order(self):
        try:
            ordered_usernames = ["user1", "user2"]
            success = Session.league_service.assign_draft_order(ordered_usernames)

            if success:
                self.status_label.setText("Draft order assigned successfully!")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to assign draft order: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def begin_draft(self):
        try:
            success = Session.league_service.begin_draft()

            if success:
                self.status_label.setText("Draft has begun!")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to begin draft: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def set_forfeit(self):
        forfeit = self.forfeit_input.text().strip()

        try:
            success = Session.league_service.set_forfeit(forfeit)
            if success:
                Session.init_aesthetics()  
                self._refresh_view()

                self.status_label.setText(f"Forfeit set!")
                self.status_label.setStyleSheet("color: #2e7d32;")

        except Exception as e:
            self.status_label.setText(f"Failed to set forfeit: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def _refresh_view(self):
        self._clear_layout(self.layout())
        self._build_ui()

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
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.client.session import Session

class LeagueView(QWidget):
    back_to_home = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        from app.client.widgets.header_bar import HeaderBar
        from app.client.widgets.footer_nav import FooterNav

        # Root layout (full page)
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ----- Header -----
        root_layout.addWidget(HeaderBar(self.app))

        # ----- Main content container -----
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        # ----- User's current league info -----
        league_name = Session.current_league_name or "None"
        league_id = Session.current_league_id or "N/A"
        league_forfeit = Session.league_forfeit or "None"

        self.league_info_label = QLabel(
            f"Current League: {league_name} (ID: {league_id})"
        )
        self.league_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_info_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #333;"
        )
        self.league_info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.forfeit_label = QLabel(
            f"Forfeit: {league_forfeit}"
        )
        self.forfeit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.forfeit_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #333;"
        )

        content_layout.addWidget(self.league_info_label)
        content_layout.addWidget(self.forfeit_label)

        # ----- Create League -----
        create_group = QGroupBox("Create League")
        create_layout = QHBoxLayout()
        self.create_input = QLineEdit()
        self.create_input.setPlaceholderText("League Name")
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_league)
        create_layout.addWidget(self.create_input)
        create_layout.addWidget(create_btn)
        create_group.setLayout(create_layout)

        # ----- Join League -----
        join_group = QGroupBox("Join League")
        join_layout = QHBoxLayout()
        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")
        join_btn = QPushButton("Join")
        join_btn.clicked.connect(self.join_league)
        join_layout.addWidget(self.join_input)
        join_layout.addWidget(join_btn)
        join_group.setLayout(join_layout)

        # ----- Leave League -----
        leave_btn = QPushButton("Leave League")
        leave_btn.clicked.connect(self.leave_league)

        # ----- Assign Draft Order -----
        draft_order_btn = QPushButton("Assign Draft Order")
        draft_order_btn.clicked.connect(self.assign_draft_order)
        draft_group = QGroupBox("Assign Draft Order")
        draft_layout = QHBoxLayout()
        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Usernames")
        draft_btn = QPushButton("Submit")
        draft_btn.clicked.connect(self.assign_draft_order)
        draft_layout.addWidget(self.draft_input)
        draft_layout.addWidget(draft_btn)
        draft_group.setLayout(draft_layout)

        # ----- Begin Draft -----
        begin_draft_btn = QPushButton("Begin Draft")
        begin_draft_btn.clicked.connect(self.begin_draft)

        # ----- Set Forfeit -----
        forfeit_btn = QPushButton("Set Forfeit")
        forfeit_btn.clicked.connect(self.set_forfeit)
        forfeit_group = QGroupBox("Set Forfeit")
        forfeit_layout = QHBoxLayout()
        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Forfeit")
        forfeit_btn = QPushButton("Submit")
        forfeit_btn.clicked.connect(self.set_forfeit)
        forfeit_layout.addWidget(self.forfeit_input)
        forfeit_layout.addWidget(forfeit_btn)
        forfeit_group.setLayout(forfeit_layout)

        self.owner_controls = QWidget()
        owner_layout = QVBoxLayout(self.owner_controls)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(10)

        owner_layout.addWidget(draft_group)
        owner_layout.addWidget(forfeit_group)

        self.leagueless_controls = QWidget()
        leagueless_layout = QVBoxLayout(self.leagueless_controls)
        leagueless_layout.setContentsMargins(0, 0, 0, 0)
        leagueless_layout.setSpacing(10)

        leagueless_layout.addWidget(create_group)
        leagueless_layout.addWidget(join_group)

        self.in_league_controls = QWidget()
        in_league_layout = QVBoxLayout(self.in_league_controls)
        in_league_layout.setContentsMargins(0, 0, 0, 0)
        in_league_layout.setSpacing(10)

        in_league_layout.addWidget(leave_btn)

        # add the owner_controls container to main content layout
        content_layout.addWidget(self.owner_controls)
        content_layout.addWidget(self.leagueless_controls)
        content_layout.addWidget(self.in_league_controls)
        self._refresh_view()

        # ----- Status label -----
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
        """)

        content_layout.addWidget(self.status_label)

        # Push content up so footer stays fixed
        content_layout.addStretch()

        root_layout.addWidget(content_widget, stretch=1)

        # ----- Footer navigation -----
        root_layout.addWidget(FooterNav(self.app))

        self.setLayout(root_layout)

    # ----- Slots wired to LeagueService -----
    def create_league(self):
        name = self.create_input.text().strip()
        if not name:
            self.status_label.setText("Please enter a league name.")
            return
        try:
            success = Session.league_service.create_then_join_league(name)
            if success:
                Session.current_league_name = name
                Session.current_league_id = success
                Session.init_aesthetics()  
                self._refresh_view()
                self.league_info_label.setText(
                    f"Current League: {name} (ID: {Session.current_league_id})"
                )
                self.status_label.setText(f"League '{name}' created successfully!")
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
                self.league_info_label.setText(
                    f"Current League: {Session.current_league_name} (ID: {Session.current_league_id})"
                )
                self.status_label.setText(f"Successfully joined league {league_id}!")
                self.status_label.setStyleSheet("color: #2e7d32;")
        except Exception as e:
            self.status_label.setText(f"Failed to join league: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def leave_league(self):
        try:
            success = Session.league_service.leave_league()
            if success:
                Session.current_league_name = None
                Session.current_league_id = None
                Session.init_aesthetics()  
                self._refresh_view()
                self.league_info_label.setText("Current League: None (ID: N/A)")
                self.forfeit_label.setText("Forfeit: None")
                self.status_label.setText("You have left the league successfully.")
                self.status_label.setStyleSheet("color: #2e7d32;")
        except Exception as e:
            self.status_label.setText(f"Failed to leave league: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def assign_draft_order(self):
        try:
            # Example placeholder: pull usernames from Session or backend
            ordered_usernames = ["user1", "user2"]  # Replace with real data
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
            Session.init_aesthetics()  
            self._refresh_view()
            if success:
                self.forfeit_label.setText(f"Forfeit: {forfeit}")
                self.status_label.setText(f"Forfeit set!")
                self.status_label.setStyleSheet("color: #2e7d32;")
        except Exception as e:
            self.status_label.setText(f"Failed to set forfeit: {e}")
            self.status_label.setStyleSheet("color: #cc0000;")

    def _refresh_view(self):
        self.owner_controls.setVisible(Session.is_league_owner)

        if Session.current_league_id == None:
            self.leagueless_controls.setVisible(True)
            self.in_league_controls.setVisible(False)
        else:
            self.leagueless_controls.setVisible(False)
            self.in_league_controls.setVisible(True)
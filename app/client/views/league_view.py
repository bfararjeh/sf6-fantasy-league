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

        # clears then builds ui
        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.footer = FooterNav(self.app)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content_widget = QWidget()

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(50, 35, 50, 35)
        self.content_layout.setSpacing(35)

        self.scroll.setWidget(self.content_widget)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(25)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
            }
        """)

        self.root_layout.addWidget(self.header)
        self.root_layout.addWidget(self.scroll, stretch=1)
        self.root_layout.addWidget(self.status_label)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        self.in_league_display = self._build_in_league_display()
        self.leagueless_controls = self._build_leagueless_controls()
        self.owner_controls = self._build_owner_controls()
        self.leave = self._build_leave_button()

        self.content_layout.addWidget(self.in_league_display)
        self.content_layout.addWidget(self.leagueless_controls)
        self.content_layout.addWidget(self.owner_controls)
        self.content_layout.addWidget(self.leave)


# -- BUILDERS --

    def _build_owner_controls(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.owner_title = QLabel("Owner Controls")
        self.owner_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.owner_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333; padding-bottom: 10px;"
        )

        # draft controls
        self.draft_controls = self._build_draft_controls()

        # forfeit controls
        self.forfeit_controls = self._build_forfeit_controls()

        layout.addWidget(self.owner_title)
        layout.addLayout(self.draft_controls)
        layout.addLayout(self.forfeit_controls)

        container.setVisible(False)
        return container

    def _build_leagueless_controls(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.leagueless_title = QLabel("Create or Join a League!")
        self.leagueless_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leagueless_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333;"
        )

        create_and_join = self._build_create_and_join_controls()

        layout.addWidget(self.leagueless_title)
        layout.addLayout(create_and_join)

        container.setVisible(False)
        return container

    def _build_in_league_display(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.league_info = self._build_league_info()
        self.draft_info_container = self._build_draft_info()

        layout.addWidget(self.league_info)
        layout.addWidget(self.draft_info_container)

        container.setVisible(False)
        return container

    def _build_leave_button(self):
        # leave league
        leave_btn = QPushButton("Leave League")
        leave_btn.setFixedWidth(100)
        leave_btn.setFixedHeight(30)
        leave_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        leave_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #bf0000;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #d10000;
            }
            QPushButton:pressed {
                background-color: #ad0000;
            }
        """)
        leave_btn.clicked.connect(self.leave_league)

        return leave_btn


# -- IN LEAGUE INFO --

    def _build_league_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.league_owner = QLabel("")
        self.league_owner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_owner.setStyleSheet("font-size: 20px; font-weight: bold; color: #7d130b;")

        self.league_name_label = QLabel("")
        self.league_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_name_label.setStyleSheet("font-size: 64px; font-weight: bold; color: #333;")

        self.league_id_label = QLabel("")
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setStyleSheet("font-size: 14px; color: #222;")

        self.forfeit_label = QLabel("")
        self.forfeit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.forfeit_label.setStyleSheet("font-size: 16px; color: #333;")

        self.league_capacity = QLabel("")
        self.league_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_capacity.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")

        self.leaguemates = QLabel("")
        self.leaguemates.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leaguemates.setStyleSheet("font-size: 18px; color: #333;")

        layout_mates = QHBoxLayout()
        layout_mates.setSpacing(10)
        layout_mates.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.league_name_label)
        layout.addWidget(self.league_id_label)
        layout.addWidget(self.league_owner)
        layout_mates.addWidget(self.leaguemates)
        layout_mates.addWidget(self.league_capacity)
        layout.addLayout(layout_mates)
        layout.addWidget(self.forfeit_label)
        layout.addWidget(self._create_separator())

        return container


# -- IN DRAFT INFO --

    def _build_draft_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(0,0,0,0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info = QLabel("Draft Order")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333; padding-bottom: 10px;"
        )

        self.draft_order_label = QLabel("")
        self.draft_order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.draft_order_label.setStyleSheet(
            "font-size: 20px; color: #333;"
        )

        self.next_pick_label = QLabel("")
        self.next_pick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_pick_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #00a8ff;"
        )

        layout.addWidget(info)
        layout.addWidget(self.draft_order_label)
        layout.addWidget(self.next_pick_label)
        layout.addWidget(self._create_separator())

        container.setVisible(False)
        return container


# -- NO LEAGUE CONTROLS --

    def _build_create_and_join_controls(self):
        # create league
        self.create_input = QLineEdit()
        self.create_input.setPlaceholderText("League Name")

        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_input)

        create_group = QGroupBox("Create League")
        create_group.setLayout(create_group_layout)

        create_btn = QPushButton("Create")
        create_btn.setFixedWidth(100)
        create_btn.setFixedHeight(30)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #019c00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #02c302;
            }
            QPushButton:pressed {
                background-color: #006a00;
            }
        """)
        create_btn.clicked.connect(self.create_league)

        # join league
        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")

        join_group_layout = QVBoxLayout()
        join_group_layout.addWidget(self.join_input)

        join_group = QGroupBox("Join League")
        join_group.setLayout(join_group_layout)

        join_btn = QPushButton("Join")
        join_btn.setFixedWidth(100)
        join_btn.setFixedHeight(30)
        join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        join_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ffcd00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ffd83a;
            }
            QPushButton:pressed {
                background-color: #d3a900;
            }
        """)
        join_btn.clicked.connect(self.join_league)

        create_row = QHBoxLayout()
        create_row.addWidget(create_group)
        create_row.addWidget(create_btn)
        create_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        join_row = QHBoxLayout()
        join_row.addWidget(join_group)
        join_row.addWidget(join_btn)
        join_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(join_row)
        layout.addLayout(create_row)
        layout.addWidget(self._create_separator())

        return layout


# -- OWNER CONTROLS --

    def _build_draft_controls(self):
        layout = QHBoxLayout()

        group = QGroupBox("Assign Draft Order")
        group.setLayout(layout)

        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Alice, Bob, Charlie") 
        layout.addWidget(self.draft_input)

        set_btn = QPushButton("Set Order")
        set_btn.setFixedWidth(100)
        set_btn.setFixedHeight(30)
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #019c00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #02c302;
            }
            QPushButton:pressed {
                background-color: #006a00;
            }
        """)
        set_btn.clicked.connect(self.assign_draft_order)

        begin_btn = QPushButton("Begin Draft")
        begin_btn.setFixedWidth(100)
        begin_btn.setFixedHeight(30)
        begin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        begin_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ffcd00;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ffd83a;
            }
            QPushButton:pressed {
                background-color: #d3a900;
            }
        """)
        begin_btn.clicked.connect(self.begin_draft)

        draft_row = QHBoxLayout()
        draft_row.addWidget(group)
        draft_row.addWidget(set_btn)
        draft_row.addWidget(begin_btn)
        draft_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return draft_row

    def _build_forfeit_controls(self):
        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Loser must...")

        layout = QVBoxLayout()
        layout.addWidget(self.forfeit_input)

        group = QGroupBox("Set Forfeit")
        group.setLayout(layout)

        btn = QPushButton("Submit")
        btn.setFixedWidth(100)
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ff5cf6;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ff92f9;
            }
            QPushButton:pressed {
                background-color: #ff3bf4;
            }
        """)
        btn.clicked.connect(self.set_forfeit)

        row = QHBoxLayout()
        row.addWidget(group)
        row.addWidget(btn)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return row


# -- BUTTON METHODS --

    def create_league(self):
        name = self.create_input.text().strip()

        if not name:
            self._set_status("Please enter a league name.", code=2)
            return

        def _success(success):
            if success:
                self._refresh()
                self._set_status("League created successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to create league: {error}", code=2)

        self._set_status("Creating League...")
        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.create_then_join_league,
            args=(name,),
            on_success=_success,
            on_error=_error
        )

    def join_league(self):
        league_id = self.join_input.text().strip()
        print("join_league: CLICK")

        if not league_id:
            self._set_status("Please enter a league ID.", code=2)
            return
        
        def _success(success):
            if success:  
                self._refresh()

                self._set_status("League joined successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to join league: {error}", code=2)

        self._set_status("Joining League...")
        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.join_league,
            args=(league_id,),
            on_success=_success,
            on_error=_error
        )

    def leave_league(self):
        print("leave_league: CLICK")

        def _success(success):
            if success:  
                self._refresh()
                self._set_status("League left successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to leave league: {error}", code=2)

        self._set_status("Leaving League...")
        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.leave_league,
            args=(),
            on_success=_success,
            on_error=_error
        )

    def assign_draft_order(self):
        usernames = self.draft_input.text().strip()
        print("assign_draft_order: CLICK")

        if not usernames:
            self._set_status("Please enter a list of usernames.", code=2)
            return

        user_list = [name.strip() for name in usernames.split(",")]

        def _success(success):
            if success:  
                self._refresh()

                self._set_status("Draft order assigned successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to assign draft order: {error}", code=2)

        self._set_status("Assignign draft order...")
        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.assign_draft_order,
            args=(user_list,),
            on_success=_success,
            on_error=_error
        )

    def begin_draft(self):
        print("begin_draft: CLICK")

        def _success(success):
            if success:  
                self._refresh()

                self._set_status("Draft started successfully! Head over to the team page to pick your players!", code=1)

        def _error(error):
            self._set_status(f"Failed to begin draft: {error}", code=2)

        self._set_status("Beginning draft...")
        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.begin_draft,
            args=(),
            on_success=_success,
            on_error=_error
        )

    def set_forfeit(self):
        forfeit = self.forfeit_input.text().strip()
        print("set_forfeit: CLICK")

        if not forfeit:
            self._set_status("Please enter a forfeit.", code=2)
            return

        def _success(success):
            if success:  
                self._refresh()
                self._set_status("Forfeit set!", code=1)

        def _error(error):
            self._set_status(f"Failed to set forfeit: {error}", code=2)

        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.set_forfeit,
            args=(forfeit,),
            on_success=_success,
            on_error=_error
        )


# -- LAYOUT STUFF

    def _refresh(self):
        Session.init_aesthetics()

        # grabbing league aesthetics
        self.my_league_name = Session.current_league_name
        self.my_league_id = Session.current_league_id
        self.my_league_forfeit = Session.league_forfeit
        self.my_capacity = f"{len(Session.leaguemates)}/5"
        self.my_leaguemates = [d['manager_name'] for d in Session.leaguemates]
        self.my_draft_order = Session.draft_order
        self.my_next_pick = Session.next_pick
        self.is_owner = Session.is_league_owner
        self.is_draft_complete = Session.draft_complete

        self._update_view()

    def _update_view(self):
        # league info
        if self.is_owner:
            self.league_owner.setText("Owner")
            self.league_owner.setVisible(True)
        else:
            self.league_owner.setVisible(False)
            
        self.league_name_label.setText(self.my_league_name or "")
        self.league_id_label.setText(f"ID: {self.my_league_id}" or "")
        self.league_capacity.setText(f"{len(self.my_leaguemates)}/5" or "")
        self.leaguemates.setText(", ".join(self.my_leaguemates) or "")

        # forfeit info
        if self.my_league_forfeit:
            self.forfeit_label.setText(
            f'<span style="font-weight:bold; color:#bf0000;">Forfeit:</span> {self.my_league_forfeit}'
        ) 
        else:
            self.forfeit_label.setText(
            f'<span style="font-weight:bold; color:#bf0000;">Forfeit not yet set.</span>'
        ) 
        
        # draft info
        has_draft = bool(self.my_draft_order)
        draft_complete = bool(self.is_draft_complete)
        self.draft_info_container.setVisible(has_draft)
        self.draft_info_container.setVisible(not draft_complete)
        if has_draft:
            self.draft_order_label.setText("Draft Order: "+", ".join(self.my_draft_order))
            self.next_pick_label.setText(f"<b>Next to Pick:</b> {self.my_next_pick}")

        # conditional controls
        self.owner_controls.setVisible(self.is_owner)
        self.leagueless_controls.setVisible(self.my_league_id is None)
        self.in_league_display.setVisible(self.my_league_id is not None)

    def _set_status(self, msg, code=0):
        if code == 1:
            color = "#2e7d32"
        elif code == 2:
            color = "#cc0000"
        else:
            color = "#333333"

        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(msg)

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
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
        # header
        self.root_layout.addWidget(HeaderBar(self.app))

        # main content
        self.content_widget = QWidget()

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(35)

        # grabbing league aesthetics
        self.league_name = Session.current_league_name or "None"
        self.league_id = Session.current_league_id or "N/A"
        self.league_forfeit = Session.league_forfeit or None
        self.is_owner = Session.is_league_owner or False
        self.capacity = f"{len(Session.leaguemates)}/5"
        self.leaguemates = [d['manager_name'] for d in Session.leaguemates]
        self.draft_order = Session.draft_order
        self.next_pick = Session.next_pick

        # defining widgets to show owner
        self.owner_controls = QWidget()
        owner_layout = QVBoxLayout(self.owner_controls)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(20)

        settings_label = QLabel("Owner Controls")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; padding-bottom: 30px;")

        owner_layout.addWidget(settings_label)
        owner_layout.addLayout(self._build_draft_settings())
        owner_layout.addLayout(self._build_forfeit_stuff())

        # defining widgets to show to those with no league
        self.leagueless_controls = QWidget()
        leagueless_layout = QVBoxLayout(self.leagueless_controls)
        leagueless_layout.setContentsMargins(0, 0, 0, 0)
        leagueless_layout.setSpacing(20)

        create_join = self._build_create_and_join()

        leagueless_label = QLabel("Create or Join a League!")
        leagueless_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leagueless_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")

        leagueless_layout.addWidget(leagueless_label)
        leagueless_layout.addLayout(create_join[0])
        leagueless_layout.addLayout(create_join[1])

        # defining widgets to show those in a league
        self.in_league_controls = QWidget()
        in_league_layout = QVBoxLayout(self.in_league_controls)
        in_league_layout.setContentsMargins(0, 0, 0, 0)
        in_league_layout.setSpacing(20)

        in_league_layout.addWidget(self._build_leave_button(), alignment=Qt.AlignmentFlag.AlignCenter)

        # status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cc0000;
            }
        """)

        # adding everything to content layout: ordered
        content_layout.addWidget(self._build_league_info())
        content_layout.addWidget(self._create_separator())
        content_layout.addWidget(self.leagueless_controls)

        if self.league_id != "N/A": 
            content_layout.addWidget(self._build_league_stats())
            content_layout.addWidget(self._create_separator())

        if self.draft_order != []: 
            content_layout.addWidget(self._build_draft_status())
            content_layout.addWidget(self._create_separator())

        content_layout.addWidget(self.owner_controls)
        content_layout.addStretch()
        content_layout.addSpacing(50)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.in_league_controls)

        self.owner_controls.setVisible(bool(Session.is_league_owner))

        if Session.current_league_id is None:
            self.leagueless_controls.setVisible(True)
            self.in_league_controls.setVisible(False)
        else:
            self.leagueless_controls.setVisible(False)
            self.in_league_controls.setVisible(True)

        scrollable = QScrollArea()
        scrollable.setWidgetResizable(True)
        scrollable.setWidget(self.content_widget)

        self.root_layout.addWidget(scrollable, stretch=1)
        self.root_layout.addWidget(FooterNav(self.app))


    def _build_league_info(self):
        # league owner, name, and id
        league_info_container = QWidget()
        league_info_layout = QVBoxLayout(league_info_container)
        league_info_layout.setSpacing(10)
        league_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.league_owner = QLabel("Owner")
        self.league_owner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_owner.setStyleSheet("font-size: 20px; font-weight: bold; color: #7d130b;")

        self.league_name_label = QLabel(f"Current League: {self.league_name}")
        self.league_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")

        self.league_id_label = QLabel(f"ID: {self.league_id}")
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setStyleSheet("font-size: 14px; color: #222;")

        if self.is_owner == True:
            league_info_layout.addWidget(self.league_owner)
        league_info_layout.addWidget(self.league_name_label)
        league_info_layout.addWidget(self.league_id_label)

        return league_info_container

    def _build_league_stats(self):
        # league users and capacity
        league_users_container = QWidget()
        league_users_layout = QVBoxLayout(league_users_container)
        league_users_layout.setSpacing(10)
        league_users_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # forfeit label only when in league
        self.forfeit_label = QLabel()
        self.forfeit_label.setText(
            f'<span style="font-weight:bold; color:#bf0000;">Forfeit:</span> {self.league_forfeit}'
        )
        self.forfeit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.forfeit_label.setStyleSheet("font-size: 16px; color: #333;")

        self.league_capacity = QLabel(f"Capacity: {self.capacity}")
        self.league_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_capacity.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")

        self.leaguemates = QLabel(f'{", ".join(self.leaguemates)}')
        self.leaguemates.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leaguemates.setStyleSheet("font-size: 18px; color: #333;")

        settings_label = QLabel("League Information")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; padding-bottom: 30px;")

        if self.league_id != "N/A": 
            league_users_layout.addWidget(settings_label)
            league_users_layout.addWidget(self.league_capacity)
            league_users_layout.addWidget(self.leaguemates)
        if self.league_forfeit is not None: league_users_layout.addWidget(self.forfeit_label)

        return league_users_container

    def _build_create_and_join(self):
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

        return [create_row, join_row]

    def _build_draft_settings(self):
        # draft order
        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Alice, Bob, Charlie") 

        draft_btn = QPushButton("Set Order")
        draft_btn.setFixedWidth(100)
        draft_btn.setFixedHeight(30)
        draft_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        draft_btn.setStyleSheet("""
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
        draft_btn.clicked.connect(self.assign_draft_order)

        draft_layout = QHBoxLayout()
        draft_layout.addWidget(self.draft_input)

        draft_group = QGroupBox("Assign Draft Order")
        draft_group.setLayout(draft_layout)

        # begin draft
        begin_draft_btn = QPushButton("Begin Draft")
        begin_draft_btn.setFixedWidth(100)
        begin_draft_btn.setFixedHeight(30)
        begin_draft_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        begin_draft_btn.setStyleSheet("""
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
        begin_draft_btn.clicked.connect(self.begin_draft)

        # begin/assign draft row
        draft_row = QHBoxLayout()
        draft_row.addWidget(draft_group)
        draft_row.addWidget(draft_btn)
        draft_row.addWidget(begin_draft_btn)
        draft_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return draft_row

    def _build_forfeit_stuff(self):
        # forfeit setter
        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Loser must...")

        forfeit_inner_layout = QVBoxLayout()
        forfeit_inner_layout.addWidget(self.forfeit_input)

        forfeit_group = QGroupBox("Set Forfeit")
        forfeit_group.setLayout(forfeit_inner_layout)

        forfeit_btn = QPushButton("Submit")
        forfeit_btn.setFixedWidth(100)
        forfeit_btn.setFixedHeight(30)
        forfeit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forfeit_btn.setStyleSheet("""
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
        forfeit_btn.clicked.connect(self.set_forfeit)

        forfeit_row = QHBoxLayout()
        forfeit_row.addWidget(forfeit_group)
        forfeit_row.addWidget(forfeit_btn)
        forfeit_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return forfeit_row

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

    def _build_draft_status(self):
        # draft order and next to pick
        draft_info_container = QWidget()
        draft_info_layout = QVBoxLayout(draft_info_container)
        draft_info_layout.setSpacing(10)
        draft_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        order_label = QLabel("Draft Order")
        order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        order_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; padding-bottom: 30px;")

        order_display = QLabel(f"{", ".join(self.draft_order)}")
        order_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        order_display.setStyleSheet("font-size: 20px; color: #333;")

        next_display = QLabel()
        next_display.setText(
            f'<span style="font-weight:bold; color:#333;">Next to Pick:</span> {self.next_pick}'
        )
        next_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        next_display.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff;")

        if self.draft_order != []: 
            draft_info_layout.addWidget(order_label)
            draft_info_layout.addWidget(order_display)
            draft_info_layout.addWidget(next_display)

        return draft_info_container


    def create_league(self):
        name = self.create_input.text().strip()

        if not name:
            self._set_status("Please enter a league name.", status_type="e")
            return

        def _success(success):
            if success:
                self._refresh_view()
                self._set_status("League created successfully!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to create league: {error}", status_type="e")

        self._set_status("Creating League...", status_type="u")
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
            self._set_status("Please enter a league ID.", status_type="e")
            return
        
        def _success(success):
            if success:  
                self._refresh_view()

                self._set_status("League joined successfully!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to join league: {error}", status_type="e")

        self._set_status("Joining League...", status_type="p")
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
                self._refresh_view()
                self._set_status("League left successfully!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to leave league: {error}", status_type="e")

        self._set_status("Leaving League...", status_type="p")
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
            self._set_status("Please enter a list of usernames.", status_type="e")
            return

        user_list = [name.strip() for name in usernames.split(",")]

        def _success(success):
            if success:  
                self._refresh_view()

                self._set_status("Draft order assigned successfully!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to assign draft order: {error}", status_type="e")

        self._set_status("Assignign draft order...", status_type="p")
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
                self._refresh_view()

                self._set_status("Draft started successfully! Head over to the team page to pick your players!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to begin draft: {error}", status_type="e")

        self._set_status("Beginning draft...", status_type="p")
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
            self._set_status("Please enter a forfeit.", status_type="e")
            return

        def _success(success):
            if success:  
                self._refresh_view()
                self._set_status("Forfeit set!", status_type="s")

        def _error(error):
            self._set_status(f"Failed to set forfeit: {error}", status_type="e")

        run_async(
            parent_widget= self.content_widget,
            fn=Session.league_service.set_forfeit,
            args=(forfeit,),
            on_success=_success,
            on_error=_error
        )


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

    def _set_status(self, msg, status_type):
        self.status_label.setText(msg)

        if status_type == "s":
            color = "#2e7d32"
        elif status_type == "e":
            color = "#cc0000"
        else:
            color = "#333333"

        self.status_label.setStyleSheet(f"color: {color};")
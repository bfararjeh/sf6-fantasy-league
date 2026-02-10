from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFontMetrics, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QGroupBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QMessageBox
)

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.async_runner import run_async
from app.client.widgets.header_bar import HeaderBar
from app.client.widgets.footer_nav import FooterNav
from app.client.theme import *

class LeagueView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        # build ui then update
        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = HeaderBar(self.app)
        self.header.refresh_button.refresh_requested.connect(lambda: self._refresh(force=1))
        self.footer = FooterNav(self.app)

        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.league_widget = QWidget()
        self.league_widget.setFixedWidth(600)
        self.league_layout = QVBoxLayout(self.league_widget)
        self.league_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.league_layout.setContentsMargins(20, 0, 20, 0)
        self.league_layout.setSpacing(20)

        self.dividor = QFrame()
        self.dividor.setFrameShape(QFrame.Shape.VLine)
        self.dividor.setLineWidth(2)
        self.dividor.setStyleSheet("color: rgba(255, 255, 255, 64);")
        self.dividor.setFixedWidth(2)

        self.team_widget = QWidget()
        self.team_widget.setFixedWidth(600)
        self.team_layout = QVBoxLayout(self.team_widget)
        self.team_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.team_layout.setContentsMargins(20, 0, 20, 20)
        self.team_layout.setSpacing(20)

        main_layout.addWidget(self.league_widget, stretch=1)
        main_layout.addWidget(self.dividor)
        main_layout.addWidget(self.team_widget, stretch=1)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(30)

        self.root_layout.addWidget(self.header)
        self.root_layout.addSpacerItem(QSpacerItem(20, 30))
        self.root_layout.addWidget(main, stretch=1)
        self.root_layout.addWidget(self.status_label)
        self.root_layout.addWidget(self.footer)

        self._build_sections()

        self.setLayout(self.root_layout)

    def _build_sections(self):
        # build league widget
        self.in_league_display = self._build_in_league_display()
        self.leagueless_controls = self._build_leagueless_controls()
        self.owner_controls = self._build_owner_controls()
        self.leave = self._build_leave_button()

        self.league_layout.addWidget(self.in_league_display)
        self.league_layout.addStretch()
        self.league_layout.addWidget(self.owner_controls)
        self.league_layout.addWidget(self.leagueless_controls)
        self.league_layout.addStretch()
        self.league_layout.addWidget(self.leave)

        # build team widget
        self.team_creator = self._build_team_creator()
        self.team_info = self._build_team_info()
        self.draft_picker = self._build_draft_picker()
        self.team_overview = self._build_roster_overview()
        self.player_stats = self._build_player_stat_section()

        self.team_layout.addWidget(self.team_info)
        self.team_layout.addWidget(self.team_overview)
        self.team_layout.addWidget(self.draft_picker)
        self.team_layout.addWidget(self.player_stats)
        self.team_layout.addWidget(self.team_creator)


# -- LEAGUE BUILDERS --

    def _build_owner_controls(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # draft controls
        self.draft_controls = self._build_owner_draft_controls()

        # forfeit controls
        self.forfeit_controls = self._build_owner_forfeit_controls()

        layout.addWidget(self.draft_controls)
        layout.addWidget(self.forfeit_controls)

        container.setVisible(False)
        return container

    def _build_leagueless_controls(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        self.leagueless_title = QLabel("Create or Join a League!")
        self.leagueless_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leagueless_title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
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
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        # leave league
        self.leave_btn = QPushButton("Leave League")
        self.leave_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.leave_btn.setStyleSheet(BUTTON_STYLESHEET_D)
        self.leave_btn.clicked.connect(self.leave_league)
        layout.addWidget(self.leave_btn)

        return container

    def _build_league_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self.league_name_label = QLabel("")
        self.league_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.league_name_label.setStyleSheet("font-weight: bold;")

        self.league_owner = QLabel("")
        self.league_owner.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.league_owner.setStyleSheet(BUTTON_STYLESHEET_D)

        layout.addWidget(self.league_name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.league_owner, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacerItem(QSpacerItem(20, 25))

        self.league_id_label = QLabel("")
        self.league_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.league_id_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.league_id_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLabel:disabled {
                color: white;
            }
        """)

        self.forfeit_label = QLabel("")
        self.forfeit_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.forfeit_label.setStyleSheet("font-weight:bold; color:#ff8168;")

        self.league_capacity = QLabel("")
        self.league_capacity.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.league_capacity.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.leaguemates = QLabel("")
        self.leaguemates.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.leaguemates.setStyleSheet("font-size: 16px;")

        league_id = QLabel("League ID:")
        forfeit = QLabel("Forfeit:")
        capacity = QLabel("Capacity:")
        leaguemates = QLabel("Leaguemates:")

        stat_layout = QVBoxLayout()
        stat_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_layout = QVBoxLayout()
        label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row = QHBoxLayout()

        stat_layout.addWidget(self.league_id_label)
        stat_layout.addWidget(self.leaguemates)
        stat_layout.addWidget(self.league_capacity)
        stat_layout.addWidget(self.forfeit_label)

        label_layout.addWidget(league_id)
        label_layout.addWidget(capacity)
        label_layout.addWidget(leaguemates)
        label_layout.addWidget(forfeit)

        row.addLayout(label_layout)
        row.addStretch()
        row.addLayout(stat_layout)

        layout.addLayout(row)

        return container

    def _build_draft_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self.draft_order_label = QLabel("N/A")
        self.draft_order_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.draft_order_label.setStyleSheet(
            "font-size: 16px;"
        )

        self.next_pick_label = QLabel("N/A")
        self.next_pick_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.next_pick_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #88ff87;"
        )

        draft_order = QLabel("Draft Order:")
        next_pick = QLabel("Next Pick:")

        stat_layout = QVBoxLayout()
        stat_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_layout = QVBoxLayout()
        label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row = QHBoxLayout()

        stat_layout.addWidget(self.draft_order_label)
        stat_layout.addWidget(self.next_pick_label)

        label_layout.addWidget(draft_order)
        label_layout.addWidget(next_pick)

        row.addLayout(label_layout)
        row.addStretch()
        row.addLayout(stat_layout)

        layout.addLayout(row)

        container.setVisible(False)
        return container

    def _build_create_and_join_controls(self):
        # create league
        self.create_league_input = QLineEdit()
        self.create_league_input.setPlaceholderText("League Name")

        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_league_input)

        create_group = QGroupBox("Create League")
        create_group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)
        create_group.setLayout(create_group_layout)

        create_btn = QPushButton("Create")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.clicked.connect(self.create_league)

        # join league
        self.join_input = QLineEdit()
        self.join_input.setPlaceholderText("League ID")

        join_group_layout = QVBoxLayout()
        join_group_layout.addWidget(self.join_input)

        join_group = QGroupBox("Join League")
        join_group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)
        join_group.setLayout(join_group_layout)

        join_btn = QPushButton("Join")
        join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        join_btn.setStyleSheet(BUTTON_STYLESHEET_A)
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

        return layout

    def _build_owner_draft_controls(self):
        layout = QHBoxLayout()

        group = QGroupBox("Assign Draft Order")
        group.setLayout(layout)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)

        self.draft_input = QLineEdit()
        self.draft_input.setPlaceholderText("Alice, Bob, Charlie") 
        layout.addWidget(self.draft_input)

        set_btn = QPushButton("Set Order")
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        set_btn.clicked.connect(self.assign_draft_order)

        begin_btn = QPushButton("Begin Draft")
        begin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        begin_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        begin_btn.clicked.connect(self.begin_draft)
        
        cont = QWidget()
        row = QHBoxLayout(cont)
        row.addWidget(group)
        row.addWidget(set_btn)
        row.addWidget(begin_btn)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return cont

    def _build_owner_forfeit_controls(self):
        layout = QVBoxLayout()

        group = QGroupBox("Set Forfeit")
        group.setLayout(layout)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)
        
        self.forfeit_input = QLineEdit()
        self.forfeit_input.setPlaceholderText("Loser must...")
        layout.addWidget(self.forfeit_input)

        btn = QPushButton("Submit")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BUTTON_STYLESHEET_A)
        btn.clicked.connect(self.set_forfeit)

        cont = QWidget()
        row = QHBoxLayout(cont)
        row.addWidget(group)
        row.addWidget(btn)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return cont


# -- TEAM BUILDERS --

    def _build_team_creator(self):
        self.team_creator_container = QWidget()

        layout = QVBoxLayout(self.team_creator_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.create_team_input = QLineEdit()
        self.create_team_input.setPlaceholderText("My Team...")

        create_group_layout = QVBoxLayout()
        create_group_layout.addWidget(self.create_team_input)

        create_group = QGroupBox("Create your Team!")
        create_group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)
        create_group.setLayout(create_group_layout)

        create_label = QLabel("Create a team here!")
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold;
        """)

        create_btn = QPushButton("Create")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_A)
        create_btn.clicked.connect(self.create_team)

        create_layout = QHBoxLayout()
        create_layout.addWidget(create_group, stretch=1)
        create_layout.addWidget(create_btn)
        create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(create_label)
        layout.addSpacing(10)
        layout.addLayout(create_layout)
        
        return self.team_creator_container

    def _build_team_info(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.team_name_label = QLabel("")
        self.team_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.team_name_label)

        return container

    def _build_draft_picker(self):
        self.pick_container = QWidget()

        layout = QVBoxLayout(self.pick_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.pick_input = QComboBox()
        player_names = [p["name"] for p in Session.player_scores]
        player_names_sorted = sorted(player_names, key=str.casefold)
        self.pick_input.addItems(player_names_sorted)
        self.pick_input.setEditable(True)
        self.pick_input.setStyleSheet("""
            QComboBox QAbstractItemView {
                color: white;
            }
        """)
        self.pick_input.setPlaceholderText("Blaz, MenaRD, Leshar...")

        group_layout = QVBoxLayout()
        group_layout.addWidget(self.pick_input)

        group = QGroupBox("Pick a Player!")
        group.setStyleSheet("""
            QGroupBox {
                color: white;
            }
        """)
        group.setLayout(group_layout)

        label = QLabel("It's your turn to pick a player!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold;
        """)

        btn = QPushButton("Pick")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BUTTON_STYLESHEET_A)
        btn.clicked.connect(self.pick_player)

        pick_layout = QHBoxLayout()
        pick_layout.addWidget(group, stretch=1)
        pick_layout.addWidget(btn, stretch=1)
        pick_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addSpacing(10)
        layout.addLayout(pick_layout)
        
        return self.pick_container

    def _build_roster_overview(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # player row
        self.team_bar_layout = QHBoxLayout()
        self.team_bar_layout.setSpacing(10)
        self.team_bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(self.team_bar_layout)

        return container

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(5)

        image = QLabel()
        image.setFixedSize(QSize(75, 75))
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        if player:
            # --- Player present ---
            player_name = player.get("id", "-")
            img_path = ResourcePath.PLAYERS / f"{player_name}.jpg"

            pixmap = QPixmap(str(img_path))
            if pixmap.isNull():
                pixmap = QPixmap(str(ResourcePath.PLAYERS / "placeholder.png"))

            image.setPixmap(
                pixmap.scaled(
                    75, 75,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            image.setStyleSheet("border: 2px solid #BBBBBB;")
            image.setCursor(Qt.CursorShape.PointingHandCursor)

        else:
            # --- Empty slot ---
            image.setStyleSheet("""
                border: 2px dashed #555;
                background-color: #333;
                color: #eee;
            """)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setText("?")

        layout.addWidget(image)

        return slot

    def _build_player_stat_section(self):
        container = QWidget()
        self.player_detail_layout = QVBoxLayout(container)
        self.player_detail_layout.setContentsMargins(50, 0, 50, 0)
        self.player_detail_layout.setSpacing(15)

        return container

    def _update_player_stat(self, player: dict):
        # prevent when pick a player visible

        if self.draft_picker.isVisible():
            print(self.draft_picker.isVisible())
            return

        # Clear previous stats
        while self.player_detail_layout.count():
            item = self.player_detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        name = player["id"]
        region = player.get("region", "Unknown")
        points = player["points"]
        joined_at = player["joined_at"]
        left_at = player["left_at"]
        active = left_at is None

        # Row container
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Player image
        image = QLabel()
        image.setStyleSheet("border: 2px solid #FFFFFF;")
        image.setFixedSize(QSize(200, 200))
        image.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        img_path = ResourcePath.PLAYERS / f"{name}.jpg"
        if not img_path.exists():
            img_path = ResourcePath.PLAYERS / "placeholder.png"
        pixmap = QPixmap(str(img_path)).scaled(200, 200, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image.setPixmap(pixmap)

        region_img = ResourcePath.FLAGS / f"{region}.png"
        if not region_img.exists():
            region_img = ResourcePath.FLAGS / "placeholder.png"

        info_label = QLabel()
        info_label.setText(
            "<div style='line-height: 1;'>"
            f"<span style='font-size:20px; font-weight: bold;;'>{name}</span><br/>"
            f"<span style='font-size:16px; color:#BBBBBB;'>{region}  </span>"
            f"<img src='{region_img}' width='18' height='12'><br/>"
            "</div>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        points_label = QLabel(f"Points: {points}")
        points_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        joined_label = QLabel(f"Joined At: {joined_at.split('T')[0]}")
        joined_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(points_label)
        layout.addWidget(joined_label)
        if not active:
            left_label = QLabel(f"Left At: {left_at.split('T')[0]}")
            left_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(QLabel("Transferred"))
            layout.addWidget(left_label)

        self.player_detail_layout.addWidget(frame)


# -- BUTTON METHODS --

    def create_league(self):
        name = self.create_league_input.text().strip()
        self.create_league_input.setText("")

        if not name:
            self._set_status("Please enter a league name.", code=2)
            return

        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("League created successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to create league: {error}", code=2)

        self._set_status("Creating League...")
        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.create_then_join_league,
            args=(name,),
            on_success=_success,
            on_error=_error
        )

    def join_league(self):
        league_id = self.join_input.text().strip()
        self.join_input.setText("")

        if not league_id:
            self._set_status("Please enter a league ID.", code=2)
            return
        
        def _success(success):
            if success:  
                self._refresh(force=1)

                self._set_status("League joined successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to join league: {error}", code=2)

        self._set_status("Joining League...")
        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.join_league,
            args=(league_id,),
            on_success=_success,
            on_error=_error
        )

    def leave_league(self):
        def _success(success):
            if success:  
                self._refresh(force=1)
                self._set_status("League left successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to leave league: {error}", code=2)

        self._set_status("Leaving League...")

        msg = QMessageBox(self)
        msg.setWindowTitle("Leave League")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Are you sure you would like to leave your league?")
        msg.setIcon(QMessageBox.Icon.Warning)

        ok_btn = msg.addButton("Leave", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        if msg.clickedButton() != ok_btn:
            self._set_status("Leave cancelled.", 2)
            return
        
        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.leave_league,
            args=(),
            on_success=_success,
            on_error=_error
        )

    def assign_draft_order(self):
        usernames = self.draft_input.text().strip()
        self.draft_input.setText("")

        if not usernames:
            self._set_status("Please enter a list of usernames.", code=2)
            return

        user_list = [name.strip() for name in usernames.split(",")]

        def _success(success):
            if success:  
                self._refresh(force=1)
                self._set_status("Draft order assigned successfully!", code=1)

        def _error(error):
            self._set_status(f"Failed to assign draft order: {error}", code=2)

        self._set_status("Assigning draft order...")
        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.assign_draft_order,
            args=(user_list,),
            on_success=_success,
            on_error=_error
        )

    def begin_draft(self):
        def _success(success):
            if success:  
                self._refresh(force=1)

                self._set_status("Draft started successfully! Head over to the team page to pick your players!", code=1)

        def _error(error):
            self._set_status(f"Failed to begin draft: {error}", code=2)

        self._set_status("Beginning draft...")

        msg = QMessageBox(self)
        msg.setWindowTitle("Begin Draft")
        msg.setStyleSheet("background: #10194D;")
        msg.setText("Beginning the draft will lock your league, preventing any member leaving or joining. Continue?")
        msg.setIcon(QMessageBox.Icon.Question)

        ok_btn = msg.addButton("Begin draft", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        if msg.clickedButton() != ok_btn:
            self._set_status("Draft cancelled.", 2)
            return

        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.begin_draft,
            args=(),
            on_success=_success,
            on_error=_error
        )

    def set_forfeit(self):
        forfeit = self.forfeit_input.text().strip()
        self.forfeit_input.setText("")

        if not forfeit:
            self._set_status("Please enter a forfeit.", code=2)
            return

        def _success(success):
            if success:
                self.my_league_forfeit = forfeit
                Session.league_forfeit = forfeit
                self._fit_text_to_width(label=self.forfeit_label, text=self.my_league_forfeit, max_width=400, max_font_size=14)
                self._set_status("Forfeit set!", code=1)

        def _error(error):
            self._set_status(f"Failed to set forfeit: {error}", code=2)

        run_async(
            parent_widget= self.league_widget,
            fn=Session.league_service.set_forfeit,
            args=(forfeit,),
            on_success=_success,
            on_error=_error
        )

    def pick_player(self):
        player = self.pick_input.currentText()
        print("pick_player: CLICK")

        if not player:
            self._set_status("Please enter a player name.", 2)
            return
        
        if not any(p["name"] == player for p in Session.player_scores):
            self._set_status(f"{player} not found. Names are case sensitive!", 2)
            return
        
        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status(f"Welcome {player} to {self.my_team_name}!", 1)
        
        def _error(error):
            self._set_status(f"Failed to pick player: {error}", 2)
        
        self._set_status("Picking player...", 0)
        run_async(
            parent_widget= self.team_widget,
            fn= Session.team_service.pick_player,
            args= (player,),
            on_success=_success,
            on_error=_error
        )

    def create_team(self):
        team_name = self.create_team_input.text().strip()
        self.create_team_input.setText("")
        print("create_team: CLICK")

        if not team_name:
            self._set_status("Please enter a team name.", 2)
        
        def _success(success):
            if success:
                self._refresh(force=1)
                self._set_status("Team created successfuly!", 1)
        
        def _error(error):
            self._set_status(f"Failed to create team: {error}", 2)
        
        self._set_status("Creating team...", 0)
        run_async(
            parent_widget= self.team_widget,
            fn = Session.team_service.create_team,
            args= (team_name,),
            on_success=_success,
            on_error=_error
        )


# -- LAYOUT STUFF

    def _refresh(self, force=0):
        Session.init_league_data(force)

        # grabbing league aesthetics
        self.my_league_name = Session.current_league_name
        self.my_league_id = Session.current_league_id
        self.my_league_forfeit = Session.league_forfeit
        leaguemates = Session.leaguemates or []
        self.my_capacity = f"{len(leaguemates)}/5"
        self.my_leaguemates = [d['manager_name'] for d in leaguemates]
        self.my_draft_order = Session.draft_order or []
        self.my_next_pick = Session.next_pick
        self.is_league_locked = Session.is_league_locked
        self.is_owner = Session.is_league_owner
        self.is_draft_complete = Session.draft_complete

        # grabbing team aesthetics
        self.my_username = Session.user
        self.my_user_id = Session.user_id
        self.my_team_name = Session.current_team_name
        self.my_team_standings = Session.my_team_standings or []

        self._update_view()

    def _update_view(self):
        # -- LEAGUE WIDGET --

        if self.is_owner:
            self.league_owner.setText("Owner")
            self.league_owner.setVisible(True)
        else:
            self.league_owner.setVisible(False)
            
        self._fit_text_to_width(label=self.league_name_label, text=self.my_league_name, max_width=400)
        self.league_id_label.setText(f"{self.my_league_id}" or "")
        self.league_capacity.setText(f"{len(self.my_leaguemates)}/5" or "")
        self.leaguemates.setText(", ".join(self.my_leaguemates) or "")

        # forfeit info
        if self.my_league_forfeit:
            self._fit_text_to_width(label=self.forfeit_label, text=self.my_league_forfeit, max_width=400, max_font_size=14)
        else:
            self.forfeit_label.setText(
            f'Forfeit not yet set.'
        ) 

        # draft info
        self.draft_info_container.setVisible(True)

        if bool(self.my_draft_order):
            self.draft_order_label.setText(", ".join(self.my_draft_order))
        if bool(self.is_league_locked):
            self.next_pick_label.setText(f"{self.my_next_pick}")
        if bool(self.is_draft_complete):
            self.draft_info_container.setVisible(False)

        if bool(self.is_league_locked) or bool(self.is_draft_complete) or not bool(self.my_league_id):
            self.leave.setVisible(False)
        else:
            self.leave.setVisible(True)

        # conditional controls
        self.owner_controls.setVisible(self.is_owner)
        self.draft_controls.setVisible(not self.is_league_locked)
        self.leagueless_controls.setVisible(self.my_league_id is None)
        self.in_league_display.setVisible(self.my_league_id is not None)
        self.team_widget.setVisible(self.my_league_id is not None)
        self.dividor.setVisible(self.my_league_id is not None)

        # -- TEAM WIDGET --

        self._update_player_slots()

        if bool(self.my_team_name):
            self.team_creator.setVisible(False)
            self.team_info.setVisible(True)
            self.team_overview.setVisible(True)
        else:
            self.team_creator.setVisible(True)
            self.team_info.setVisible(False)
            self.team_overview.setVisible(False)

        self.draft_picker.setVisible(
            bool(self.my_team_name) and 
            not self.is_draft_complete and 
            (self.my_username == self.my_next_pick) and 
            self.is_league_locked
        )

        self._fit_text_to_width(label=self.team_name_label, text=self.my_team_name, max_width=400)

    def _update_player_slots(self):
        players = self.my_team_standings.get("players", []) if self.my_team_standings else []
        players.sort(key=lambda p: (p["left_at"] is not None, -datetime.fromisoformat(p["left_at"]).timestamp() if p["left_at"] else 0))

        # clear old slots
        for i in reversed(range(self.team_bar_layout.count())):
            widget = self.team_bar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.player_buttons = []
        
        for i in range(5):
            if i < len(players):
                slot = self._build_player_slot(players[i])
                slot.mousePressEvent = lambda e, p=players[i]: self._update_player_stat(p)
                self.player_buttons.append(slot)
            else:
                slot = self._build_player_slot({})
            self.team_bar_layout.addWidget(slot, stretch=1)

    def _set_status(self, msg, code=0):
        colors = {0: "#FFFFFF", 1: "#00ff0d", 2: "#FFD700"}
        self.status_label.setStyleSheet((f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {colors.get(code, '#FFFFFF')};
            }}
        """))
        self.status_label.setText(msg)

        if hasattr(self, "_status_timer") and self._status_timer.isActive():
            self._status_timer.stop()

        # Create a new timer to clear the label
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status_label.setText(""))
        self._status_timer.start(8000)

    def _fit_text_to_width(self, label: QLabel, text: str, max_width: int,
                        min_font_size=2, max_font_size=40):
        """
        Adjust the font size of a QLabel so that `text` fits within `max_width`.
        This version is stable against repeated calls and shrinking.
        """
        if not text or max_width <= 0:
            return

        # Start with min font size
        font = label.font()
        font.setBold(True)  # preserve bold if needed
        font_size = min_font_size
        font.setPointSize(font_size)
        metrics = QFontMetrics(font)

        # Binary search to find the largest font that fits
        low, high = min_font_size, max_font_size
        best_size = min_font_size

        while low <= high:
            mid = (low + high) // 2
            font.setPointSize(mid)
            metrics = QFontMetrics(font)
            if metrics.boundingRect(text).width() <= max_width:
                best_size = mid  # fits, try bigger
                low = mid + 1
            else:
                high = mid - 1  # too big, try smaller
                
        font.setPointSize(best_size)
        label.setFont(font)
        label.setText(text)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh(force=0)

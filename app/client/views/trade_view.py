from datetime import datetime, timezone

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.client.controllers.async_runner import run_async
from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager

from app.client.widgets.hover_image import HoverImage
from app.client.widgets.misc import _build_empty_label, set_status
from app.client.widgets.spinner import SpinnerWidget
from app.client.widgets.utp_carousel import _UTPCarousel

from app.client.theme import *

class TradeView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self._build_static()
        self._refresh()

    def _build_static(self):
        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(50, 15, 50, 15)
        content_layout.setSpacing(50)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(30)

        # stack switches between countdown and trade page
        self.view_stack = QStackedWidget()

        self._spinner_page = self._build_spinner_page()
        self.view_stack.addWidget(self._spinner_page)

        content_layout.addWidget(self._build_title())
        content_layout.addWidget(self.view_stack)

        self.root_layout.addWidget(content_widget, stretch=1)
        self.root_layout.addWidget(self.status_label)


# -- COMMON BUILDERS --

    def _build_title(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)

        trades = QLabel("Trades")
        trades.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trades.setStyleSheet("font-size: 64px; font-weight: bold;")

        layout.addWidget(trades)

        self._history_btn = QPushButton("Trade History")
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.clicked.connect(self._toggle_history)
        self._history_btn.setStyleSheet(BUTTON_STYLESHEET_A)

        left = QWidget()
        center = QWidget()
        right = QWidget()

        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(trades, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 10, 0)
        right_layout.addStretch()
        right_layout.addWidget(self._history_btn, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addWidget(left, 1)
        layout.addWidget(center)
        layout.addWidget(right, 1)

        return container


# -- COUNTDOWN BUILDERS --

    def _build_countdown_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._build_countdown())
        layout.addStretch()
        layout.addWidget(self._build_window_list())

        return widget

    def _build_countdown(self):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: white; "
            "background-color: #b0131e; padding: 10px 20px; border-radius: 8px;"
        )

        if self.next_window:
            start = datetime.fromisoformat(self.next_window["start_date"])
            sub_label = QLabel(f"Trade window opens at {start.strftime('%B %d')} 00:00 UTC.")
        else:
            sub_label = QLabel("No upcoming trade windows.")

        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")

        layout.addWidget(self.countdown_label)
        layout.addWidget(sub_label)

        if self.next_window:
            self.timer = QTimer()
            self.timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.timer.timeout.connect(self._tick)
            self.timer.start(500)
            self._tick()
        else:
            self.countdown_label.setText("--d --h --m --s")

        return container

    def _build_window_list(self):
        now = datetime.now(timezone.utc)

        container = QWidget()
        container.setFixedWidth(500)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        for w in self.trade_windows:
            start = datetime.fromisoformat(w["start_date"])
            end   = datetime.fromisoformat(w["end_date"])
            is_next = self.next_window and w["id"] == self.next_window["id"]
            is_past = end < now

            row = QWidget()
            row.setObjectName("row")
            row.setStyleSheet(f"""
                QWidget#row {{
                    background-color: {"#1f301f" if is_next else "#0d0d1a"};
                    border: 1px solid;
                    border-radius: 6px;
                    border-color: {"#3EA702" if is_next else ("#555555" if is_past else "#1F4768")};
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(15, 10, 15, 10)

            date_label = QLabel(f"{start.strftime('%b %d')} to {end.strftime('%b %d, %Y')}")
            date_label.setStyleSheet(f"font-size: 14px; color: {"#686868" if is_past else 'white'};")

            tag_text = "Next" if is_next else ("Past" if is_past else "Upcoming")
            tag_color = "#3EA702" if is_next else ("#555555" if is_past else "#339FF8")
            tag = QLabel(tag_text)
            tag.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {tag_color};")
            tag.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(date_label)
            row_layout.addStretch()
            row_layout.addWidget(tag)

            layout.addWidget(row)

        return container


# -- TRADING BUILDERS --

    def _build_selection_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cont = QWidget()
        main = QHBoxLayout(cont)
        main.setContentsMargins(0,0,0,0)

        main.addWidget(self._build_trade_card(
            image_path=str(ResourcePath.IMAGES / "u2p.png"),
            title="Market Trade",
            desc="Trade with any free player in the open player pool.",
            on_click=lambda: self._go_to_utp()
        ))

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("color: #444444;")
        main.addWidget(divider)

        main.addWidget(self._build_trade_card(
            image_path=str(ResourcePath.IMAGES / "u2u.png"),
            title="Manager Trade",
            desc="Accept, reject, and create trades for owned players.",
            on_click=lambda: self._go_to_utu(),
            tag=True
        ))

        layout.addWidget(cont)

        self.remaining = QLabel(f"{self.trades_remaining} trades remaining!")
        self.remaining.setStyleSheet(
        "font-size: 16px; font-weight: bold; color: white; "
        "background-color: #b0131e; padding: 5px 10px; border-radius: 8px;"
        )

        layout.addStretch()
        layout.addWidget(self.remaining, alignment=Qt.AlignmentFlag.AlignCenter)

        return widget

    def _build_trade_card(self, image_path, title, desc, on_click, tag=False,):
        card = QWidget()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("QWidget { background: transparent; }")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 48px; color: #FFFFFF;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel(desc)
        sub.setStyleSheet("font-size: 16px; color: #AAAAAA;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)

        pixmap = QPixmap(image_path)
        image = HoverImage(pixmap, size=250, hover_scale=1.08)

        layout.addWidget(label)
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        if tag:
            notif = QLabel(f"{len(self.trade_requests)} pending requests.")
            notif.setFixedHeight(22)
            notif.setStyleSheet(f"""
                font-size: 11px; font-weight: bold;
                color: {"#C6DFC3"};
                background-color: {"#02830D"};
                border: 1px solid {"#16C506"};
                border-radius: 4px;
                padding: 2px 10px;
            """)
            notif.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            layout.addWidget(notif, alignment=Qt.AlignmentFlag.AlignCenter)
        
        else:
            layout.addSpacerItem(QSpacerItem(0,38))
        
        layout.addStretch()

        image.mousePressEvent = lambda e: on_click()

        return card

    def _build_utp_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        bar = QWidget()
        button_row = QHBoxLayout(bar)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(20)

        # state
        self._utp_selected_pool_player = None
        self._utp_selected_my_player = None

        layout.addStretch()
        layout.addWidget(self._build_utp_carousel())
        layout.addStretch()
        layout.addWidget(self._build_utp_roster())

        button_row.addStretch()
        button_row.addWidget(self._build_utp_confirm_button(),alignment=Qt.AlignmentFlag.AlignCenter)
        button_row.addWidget(self._build_utp_back_button(),alignment=Qt.AlignmentFlag.AlignCenter)
        button_row.addStretch()

        layout.addWidget(bar)

        return page

    def _build_utu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # main columns
        columns = QWidget()
        columns_layout = QHBoxLayout(columns)
        columns_layout.setSpacing(20)
        columns_layout.setContentsMargins(0, 0, 0, 0)

        incoming = [r for r in self.trade_requests if r["receiver_id"] == self.my_user_id]
        outgoing = [r for r in self.trade_requests if r["initiator_id"] == self.my_user_id]

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("color: #444444;")

        columns_layout.addWidget(self._build_utu_column("Incoming Requests", incoming, outgoing=False), stretch=1)
        columns_layout.addWidget(divider)
        columns_layout.addWidget(self._build_utu_column("Outgoing Requests", outgoing, outgoing=True), stretch=1)

        # buttons
        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(20)

        create_btn = QPushButton("Request")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(BUTTON_STYLESHEET_F)
        create_btn.setFixedWidth(100)
        create_btn.clicked.connect(lambda: None)

        back_btn = QPushButton("Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(BUTTON_STYLESHEET_E)
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.view_stack.setCurrentWidget(self._selection_page))

        buttons_layout.addStretch()
        buttons_layout.addWidget(create_btn)
        buttons_layout.addWidget(back_btn)
        buttons_layout.addStretch()

        layout.addWidget(columns, stretch=1)
        layout.addWidget(buttons)

        return page

    def _build_history_page(self):
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 0, 15, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setWidget(cont)

        windows_by_id = {w["id"]: w for w in self.trade_windows}
        trades_by_window = {}
        for trade in self.trade_history:
            wid = trade["trade_window_id"]
            trades_by_window.setdefault(wid, []).append(trade)

        for wid in sorted(trades_by_window.keys(), reverse=True):
            window = windows_by_id.get(wid)
            if window:
                start = datetime.fromisoformat(window["start_date"]).strftime("%b %d")
                end = datetime.fromisoformat(window["end_date"]).strftime("%b %d, %Y")
                header_text = f"Window: {start} - {end}"
            else:
                header_text = f"Window {wid}"

            header = QLabel(header_text)
            header.setStyleSheet("""
                font-size: 15px;
                font-weight: bold;
                color: #AAAAAA;
                border-bottom: 1px solid #333333;
                padding-bottom: 6px;
            """)
        
        return scroll


# -- U2P BUILDERS --

    def _build_utp_carousel(self):
        self._utp_carousel_index = 0
        self._utp_carousel_frozen = False

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        search = QLineEdit()
        search.setFixedWidth(250)
        search.setPlaceholderText("Search players...")
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(75)
        self._search_timer.timeout.connect(self._utp_on_search)
        search.textChanged.connect(self._on_search_text_changed)

        self._utp_carousel_name_label = QLabel("Select a player")
        self._utp_carousel_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._utp_carousel_name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")

        self._utp_carousel_widget = _UTPCarousel(
            players=self.trade_players,
            get_pixmap=lambda name: Session.get_pixmap("players", name),
            on_select=self._utp_on_pool_select,
            on_hover=self._utp_on_carousel_hover
        )

        layout.addWidget(search, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._utp_carousel_name_label)
        layout.addWidget(self._utp_carousel_widget)
        return container

    def _on_search_text_changed(self, text):
        self._pending_search = text
        self._search_timer.start()

    def _utp_on_search(self):
        text = getattr(self, "_pending_search", "")
        if not text:
            self._utp_carousel_widget.set_players(self.trade_players)
        else:
            filtered = [p for p in self.trade_players if text.lower() in p["name"].lower()]
            self._utp_carousel_widget.set_players(filtered)

    def _utp_on_carousel_hover(self, player):
        if self._utp_carousel_frozen:
            return
        name = player["name"] if player else "Select a player"
        self._utp_carousel_name_label.setText(name)

    def _build_utp_confirm_button(self):
        self.utp_confirm_btn = QPushButton("Confirm")
        self.utp_confirm_btn.setEnabled(False)
        self.utp_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.utp_confirm_btn.setStyleSheet(BUTTON_STYLESHEET_F)
        self.utp_confirm_btn.setFixedWidth(100)
        self.utp_confirm_btn.clicked.connect(self._utp_on_confirm)
        return self.utp_confirm_btn

    def _build_utp_roster(self):
        self._utp_slot_widgets = {}

        cont = QWidget()
        layout = QHBoxLayout(cont)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for player in self.my_team_data:
            slot = self._build_player_slot(player)
            self._utp_slot_widgets[player["player_name"]] = slot
            layout.addWidget(slot)

        return cont

    def _build_player_slot(self, player: dict):
        slot = QWidget()
        slot.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(slot)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(5)

        player_name = player.get("player_name", "-")
        player_joined = player.get("joined_at", "-").split("T")[0]
        pixmap = Session.get_pixmap("players", player_name)

        image = HoverImage(pixmap, size=135)
        name = QLabel(player_name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-size: 16px; font-weight: bold;")

        joined = QLabel(player_joined)
        joined.setAlignment(Qt.AlignmentFlag.AlignCenter)
        joined.setStyleSheet("font-size: 12px; color: #BBBBBB;")

        layout.addWidget(image)
        layout.addWidget(name)
        layout.addWidget(joined)

        slot.mousePressEvent = lambda e, p=player: self._utp_on_roster_select(p)

        return slot

    def _utp_refresh_roster(self):
        for player_name, slot in self._utp_slot_widgets.items():
            selected = (
                self._utp_selected_my_player is not None
                and self._utp_selected_my_player.get("player_name") == player_name
            )
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(1.0 if selected or self._utp_selected_my_player is None else 0.35)
            slot.setGraphicsEffect(opacity_effect)

    def _build_utp_back_button(self):
        def _push():
            self.view_stack.setCurrentWidget(self._selection_page)
            SoundManager.play("button")

        back = QPushButton("Back")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(BUTTON_STYLESHEET_E)
        back.setFixedWidth(100)
        back.clicked.connect(lambda: _push())
        return back

    def _utp_check_confirm(self):
        ready = self._utp_selected_pool_player is not None and self._utp_selected_my_player is not None
        self.utp_confirm_btn.setEnabled(ready)

    def _utp_on_pool_select(self, player):
        if self._utp_selected_pool_player == player:
            self._utp_selected_pool_player = None
        else:
            self._utp_selected_pool_player = player
        self._utp_refresh_carousel()
        self._utp_check_confirm()

    def _utp_on_roster_select(self, player):
        if self._utp_selected_my_player == player:
            self._utp_selected_my_player = None
        else:
            self._utp_selected_my_player = player
        self._utp_refresh_roster()
        self._utp_check_confirm()

    def _utp_refresh_carousel(self):
        self._utp_carousel_widget.set_selected(self._utp_selected_pool_player)
        if self._utp_selected_pool_player:
            self._utp_carousel_name_label.setText(self._utp_selected_pool_player["name"])

    def _utp_on_confirm(self):
        pool_name = self._utp_selected_pool_player["name"]
        my_name = self._utp_selected_my_player["player_name"]

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Trade")
        msg.setStyleSheet("background: #10194D;")
        msg.setText(f"Trade {my_name} to the pool in exchange for {pool_name}?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        confirm = msg.addButton("Confirm", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("button")
        msg.exec()

        if msg.clickedButton() != confirm:
                set_status(self, "Trade cancelled.", 2)
                return

        def _success(success):
            if success:
                self._refresh(force=1)
                set_status(self, "Player traded successfully!", code=1)

        def _error(error):
            if getattr(error, "message"):
                set_status(self, f"Failed to trade player: {getattr(error, "message")}", code=2)
            else:
                set_status(self, f"Failed to trade player: {error}", code=2)

        set_status(self, "Trading player...")
        run_async(
            parent_widget=self.view_stack, 
            fn=Session.trade_service.create_pool_request,
            args=(my_name, pool_name,), 
            on_success=_success, 
            on_error=_error
        )


# -- U2U BUILDERS --

    def _build_utu_column(self, title, requests, outgoing):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(SCROLL_STYLESHEET)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setStyleSheet("")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if outgoing == True:
            scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        else:
            scroll.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        for r in requests:
            if outgoing:
                content_layout.addWidget(self._build_outgoing_request(r))
            else:
                content_layout.addWidget(self._build_incoming_request(r))

        if not requests:
            empty = _build_empty_label()
            content_layout.addStretch()
            content_layout.addWidget(empty, alignment=Qt.AlignmentFlag.AlignCenter)
            content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(label)
        layout.addWidget(scroll, stretch=1)
        layout.addSpacerItem(QSpacerItem(0, 10))

        return container

    def _build_incoming_request(self, r):
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background-color: #0d0d1a;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # top row: image + info
        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # init player
        pixmap = Session.get_pixmap("players", r["initiator_player"])
        image = HoverImage(pixmap, size=140)
        label = QLabel(f"You Get\n{r["initiator_player"]}")
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {"#36D136"};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        player = QWidget()
        play_lay = QVBoxLayout(player)
        play_lay.addWidget(image)
        play_lay.addWidget(label)

        top_layout.addStretch()
        top_layout.addWidget(player)
        top_layout.addStretch()

        # receive player
        pixmap = Session.get_pixmap("players", r["receiver_player"])
        image = HoverImage(pixmap, size=140)
        label = QLabel(f"You Give\n{r["receiver_player"]}")
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {"#FF4545"};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        player = QWidget()
        play_lay = QVBoxLayout(player)
        play_lay.addWidget(image)
        play_lay.addWidget(label)

        top_layout.addWidget(player)
        top_layout.addStretch()

        # info
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)

        created = datetime.fromisoformat(r["created_at"]).strftime("%d %b, %H:%M")
        initiator_name = self._get_username(r["initiator_id"])

        image = QLabel()
        image.setPixmap(
            Session.get_pixmap("avatars", str(r["initiator_id"])).scaled(
                75, 75,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        # buttons
        btns = QWidget()
        btns_layout = QVBoxLayout(btns)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(10)

        accept = QPushButton("O")
        accept.setCursor(Qt.CursorShape.PointingHandCursor)
        accept.setStyleSheet(BUTTON_STYLESHEET_F)
        accept.setFixedSize(QSize(35, 35))
        accept.clicked.connect(lambda: self._utu_on_accept(r))

        reject = QPushButton("X")
        reject.setCursor(Qt.CursorShape.PointingHandCursor)
        reject.setStyleSheet(BUTTON_STYLESHEET_E)
        reject.setFixedSize(QSize(35, 35))
        reject.clicked.connect(lambda: self._utu_on_reject(r))

        btns_layout.addStretch()
        btns_layout.addWidget(accept)
        btns_layout.addWidget(reject)
        btns_layout.addStretch()

        bottom = QWidget()
        bot_layout = QHBoxLayout(bottom)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.setSpacing(10)

        info_layout.addWidget(self._utu_info_label(f"From: {initiator_name}", bold=True, big=True))
        info_layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self._utu_info_label(created, color="#888888"))

        bot_layout.addStretch()
        bot_layout.addWidget(info)
        bot_layout.addSpacerItem(QSpacerItem(25, 0))
        bot_layout.addWidget(btns)
        bot_layout.addStretch()

        layout.addWidget(top)
        layout.addWidget(bottom)

        return card

    def _build_outgoing_request(self, r):
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background-color: #0d0d1a;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # top row: images
        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # initiator player (you give)
        pixmap = Session.get_pixmap("players", r["initiator_player"])
        image = HoverImage(pixmap, size=140)
        label = QLabel(f"You Give\n{r['initiator_player']}")
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #FF4545;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player = QWidget()
        play_lay = QVBoxLayout(player)
        play_lay.addWidget(image)
        play_lay.addWidget(label)
        top_layout.addStretch()
        top_layout.addWidget(player)
        top_layout.addStretch()

        # receiver player (you get)
        pixmap = Session.get_pixmap("players", r["receiver_player"])
        image = HoverImage(pixmap, size=140)
        label = QLabel(f"You Get\n{r['receiver_player']}")
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #36D136;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player = QWidget()
        play_lay = QVBoxLayout(player)
        play_lay.addWidget(image)
        play_lay.addWidget(label)
        top_layout.addWidget(player)
        top_layout.addStretch()

        # bottom row: info + cancel button
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)

        created = datetime.fromisoformat(r["created_at"]).strftime("%d %b, %H:%M")
        receiver_name = self._get_username(r["receiver_id"])

        avatar = QLabel()
        avatar.setPixmap(
            Session.get_pixmap("avatars", str(r["receiver_id"])).scaled(
                75, 75,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        info_layout.addWidget(self._utu_info_label(f"To: {receiver_name}", bold=True, big=True))
        info_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self._utu_info_label(created, color="#888888"))

        # cancel button
        btns = QWidget()
        btns_layout = QVBoxLayout(btns)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(10)

        cancel = QPushButton("X")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(BUTTON_STYLESHEET_E)
        cancel.setFixedSize(QSize(35, 35))
        cancel.clicked.connect(lambda: self._utu_on_cancel(r))

        btns_layout.addStretch()
        btns_layout.addWidget(cancel)
        btns_layout.addStretch()

        bottom = QWidget()
        bot_layout = QHBoxLayout(bottom)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.setSpacing(10)
        bot_layout.addStretch()
        bot_layout.addWidget(info)
        bot_layout.addSpacerItem(QSpacerItem(25, 0))
        bot_layout.addWidget(btns)
        bot_layout.addStretch()

        layout.addWidget(top)
        layout.addWidget(bottom)

        return card

    def _utu_info_label(self, text, bold=False, color="#FFFFFF", big=False):
        label = QLabel(text)
        label.setStyleSheet(f"font-size: {"16px" if big else "13px"}; font-weight: {'bold' if bold else 'normal'}; color: {color};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _get_username(self, user_id):
        for d in (self.leaguemate_data or []):
            if d["user_id"] == user_id:
                return d["user_name"]
        return "Unknown"

    def _utu_on_accept(self, r):
        msg = QMessageBox(self)
        msg.setWindowTitle("Accept Trade")
        msg.setStyleSheet("background: #10194D;")
        msg.setText(f"Accept {self._get_username(r['initiator_id'])}'s offer of {r['initiator_player']} for {r['receiver_player']}?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        msg.addButton("Accept", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("button")
        result = msg.exec()
        if result == 0:
            set_status("Accepting Request...")
            self._utu_execute_accept(r)

    def _utu_on_reject(self, r):
        msg = QMessageBox(self)
        msg.setWindowTitle("Reject Trade")
        msg.setStyleSheet("background: #10194D;")
        msg.setText(f"Reject {self._get_username(r['initiator_id'])}'s offer of {r['initiator_player']} for {r['receiver_player']}?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        msg.addButton("Reject", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("button")
        result = msg.exec()
        if result == 0:
            self._utu_execute_reject(r)

    def _utu_on_cancel(self, r):
        msg = QMessageBox(self)
        msg.setWindowTitle("Cancel Request")
        msg.setStyleSheet("background: #10194D;")
        msg.setText(f"Cancel your request of {r['initiator_player']} for {r['receiver_player']}?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        msg.addButton("Cancel Request", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Back", QMessageBox.ButtonRole.RejectRole)
        SoundManager.play("button")
        result = msg.exec()
        if result == 0:
            self._utu_execute_cancel(r)

    def _utu_execute_accept(self, r):
        pass

    def _utu_execute_reject(self, r):
        pass

    def _utu_execute_cancel(self, r):
        pass


# -- HISTORY BUILDERS --

    def _build_history_section(self, h):
        frame = QFrame()
        frame.setObjectName("hFrame")
        frame.setStyleSheet("""
            QFrame#hFrame {
                background-color: #090E2B;
                border: 2px solid #444444;
                border-radius: 4px;
            }
        """)

        root_layout = QVBoxLayout(frame)
        root_layout.setSpacing(15)

    
    def _build_avatar(self, user_id, size):
        image = QLabel()
        image.setPixmap(
            Session.get_pixmap("avatars", str(user_id)).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        return image


# -- NAVIGATION

    def _go_to_utp(self):
        self._show_spinner()
        QApplication.processEvents()
        QTimer.singleShot(0, self._load_utp)

    def _load_utp(self):
        if hasattr(self, "_utp_page"):
            self.view_stack.removeWidget(self._utp_page)
            self._utp_page.deleteLater()
        self._utp_page = self._build_utp_page()
        self.view_stack.addWidget(self._utp_page)
        self.view_stack.setCurrentWidget(self._utp_page)
        SoundManager.play("loaded")

    def _go_to_utu(self):
        self._show_spinner()
        QApplication.processEvents()
        QTimer.singleShot(0, self._load_utu)

    def _load_utu(self):
        if hasattr(self, "_utu_page"):
            self.view_stack.removeWidget(self._utu_page)
            self._utu_page.deleteLater()
        self._utu_page = self._build_utu_page()
        self.view_stack.addWidget(self._utu_page)
        self.view_stack.setCurrentWidget(self._utu_page)
        SoundManager.play("loaded")

    def _toggle_history(self):
        if self.view_stack.currentWidget() == getattr(self, "_history_page", None):
            self.view_stack.setCurrentWidget(self._selection_page)
            self._history_btn.setText("Trade History")
        else:
            self._go_to_history()
            self._history_btn.setText("Trade Page")

    def _go_to_history(self):
        if not hasattr(self, "_history_page"):
            self._history_page = self._build_history_page()
            self.view_stack.addWidget(self._history_page)
        self.view_stack.setCurrentWidget(self._history_page)

# -- HELPERS --

    def _determine_view(self):
        window_state = bool(self.current_window)
        if getattr(self, "_last_window_state", None) != window_state:
            self._invalidate_pages()
            self._last_window_state = window_state

        if self.current_window:
            if not hasattr(self, "_selection_page"):
                self._selection_page = self._build_selection_page()
                self.view_stack.addWidget(self._selection_page)
            self.view_stack.setCurrentWidget(self._selection_page)

        else:
            if not hasattr(self, "_countdown_page"):
                self._countdown_page = self._build_countdown_page()
                self.view_stack.addWidget(self._countdown_page)
            self.view_stack.setCurrentWidget(self._countdown_page)

    def _invalidate_pages(self):
        for attr in ("_countdown_page", "_selection_page", "_utp_page", "_utu_page", "_history_page"):
            if hasattr(self, attr):
                widget = getattr(self, attr)
                self.view_stack.removeWidget(widget)
                widget.deleteLater()
                delattr(self, attr)

    def _build_spinner_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0,0,0,105)
        self._spinner = SpinnerWidget(size=48, color="#4200FF")
        layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _show_spinner(self):
        self.view_stack.setCurrentWidget(self._spinner_page)
        self._spinner.start()

    def _hide_spinner(self):
        self._spinner.stop()

    def _tick(self):
        if self.current_window:
            return
        remaining = datetime.fromisoformat(self.next_window["start_date"]) - datetime.now(timezone.utc)
        total_seconds = int(remaining.total_seconds())
        if total_seconds <= 0:
            self.countdown_label.setText("00d 00h 00m 00s")
            self.timer.stop()
            if self.isVisible():
                QTimer.singleShot(500, self._refresh)
                SoundManager.play("boot")
            else:
                self._pending_refresh = True
            return
        days    = total_seconds // 86400
        hours   = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.countdown_label.setText(f"{days:02d}d {hours:02d}h {minutes:02d}m {seconds:02d}s")

    def _refresh(self, force=0):
        Session.init_trade_data(force)
        Session.init_leaderboards(force)

        self.my_username = Session.user
        self.my_user_id = Session.user_id

        self.leaguemate_data = Session.leaguemate_standings or []
        self.my_team_data = next((team["players"] for team in self.leaguemate_data if team["user_id"] == self.my_user_id), [])

        self.trade_windows = Session.trade_windows or []
        self.trade_requests = Session.trade_requests or []
        self.trade_players = Session.trade_players or []
        self.trade_history = Session.trade_history or []

        now = datetime.now(timezone.utc)
        parsed = [
            {
                **w,
                "start": datetime.fromisoformat(w["start_date"]),
                "end": datetime.fromisoformat(w["end_date"])
            }
            for w in self.trade_windows
        ]

        self.current_window = next((w for w in parsed if w["start"] <= now <= w["end"]), None)
        self.next_window = next((w for w in sorted(parsed, key=lambda w: w["start"]) if w["start"] > now), None)

        self.trades_remaining = 0
        if self.current_window:
            self.trades_remaining = 2 - sum(
                1
                for d in self.trade_history
                if d.get("initiator_id") == self.my_user_id
                and d.get("trade_window_id") == self.current_window.get("id")
            )

        if getattr(self, "remaining", None):
            self.remaining.setText(f"{self.trades_remaining} trades remaining!")

        new_fingerprint = (
            bool(self.current_window),
            self.current_window.get("id") if self.current_window else None,
            self.next_window.get("id") if self.next_window else None,
            self.trades_remaining,
            tuple(p["name"] for p in self.trade_players),
            tuple(r["request_id"] for r in self.trade_requests),
        )

        if getattr(self, "_last_fingerprint", None) == new_fingerprint:
            return
        

        self._last_fingerprint = new_fingerprint
        self._determine_view()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_pending_refresh", False):
            self._pending_refresh = False
            self._refresh()
            SoundManager.play("boot")
        else:
            self._refresh()

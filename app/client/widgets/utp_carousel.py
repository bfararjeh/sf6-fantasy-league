from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget
from app.client.theme import *

class _UTPCarousel(QWidget):
    def __init__(self, players, get_pixmap, on_select, on_hover, parent=None):
        super().__init__(parent)
        self._all_players = players
        self._all_pixmaps = [get_pixmap(p["name"]) for p in players]
        self._players = players
        self._pixmaps = self._all_pixmaps[:]
        self._get_pixmap = get_pixmap
        self._on_select = on_select
        self._index = 0.0          # float for smooth animation
        self._target_index = 0     # int snap target
        self._selected = None
        self._frozen = False
        self._drag_start_x = None
        self._drag_delta = 0

        self._anim_timer = QTimer()
        self._anim_timer.setInterval(8)  # ~120fps
        self._anim_timer.timeout.connect(self._animate)

        self._on_hover = on_hover

        self.setFixedHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


    def set_selected(self, player):
        self._selected = player
        self._frozen = player is not None
        self.update()

    def _snap_to(self, index):
        if len(self._players) > 7:
            self._target_index = index % len(self._players)
        else:
            self._target_index = max(0, min(index, len(self._players) - 1))
        self._anim_timer.start()

    def _animate(self):
        diff = self._target_index - self._index
        
        # take the short path around the wrap
        if len(self._players) > 7:
            n = len(self._players)
            if diff > n / 2:
                diff -= n
            elif diff < -n / 2:
                diff += n

        if abs(diff) < 0.01:
            self._index = float(self._target_index)
            self._anim_timer.stop()
        else:
            self._index += diff * 0.2
            # keep _index in range
            if len(self._players) > 7:
                self._index %= len(self._players)

        nearest = self._players[round(self._index) % len(self._players)] if self._players else None
        self._on_hover(nearest)
        self.update()

    def mousePressEvent(self, event):
        if self._frozen:
            # allow unselect by clicking selected card
            hit = self._card_at(event.pos().x())
            if hit is not None and self._players[hit] == self._selected:
                self._on_select(self._players[hit])
            return
        self._drag_start_x = event.pos().x()
        self._drag_delta = 0

    def mouseMoveEvent(self, event):
        if self._frozen or self._drag_start_x is None:
            return
        self._drag_delta = event.pos().x() - self._drag_start_x
        self._index = self._target_index - (self._drag_delta / self._card_width())
        self.update()

    def mouseReleaseEvent(self, event):
        if self._frozen:
            return
        if self._drag_start_x is not None and abs(self._drag_delta) < 8:
            # treat as click
            hit = self._card_at(event.pos().x())
            if hit is not None:
                self._snap_to(hit)
                QTimer.singleShot(180, lambda: self._on_select(self._players[hit]))
        else:
            # snap to nearest
            self._snap_to(round(self._index))
        self._drag_start_x = None
        self._drag_delta = 0

    def wheelEvent(self, event):
        if self._frozen:
            return
        delta = event.angleDelta().y()
        if delta < 0:
            self._snap_to(self._target_index + 1)
        else:
            self._snap_to(self._target_index - 1)

    def _card_width(self):
        return self.width() // 7

    def _card_at(self, x):
        center_x = self.width() // 2
        card_w = self._card_width()
        for i, _ in enumerate(self._players):
            offset = (i - self._index) * card_w
            cx = center_x + offset
            if abs(cx - x) < card_w // 2:
                return i
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        try:
            center_x = self.width() // 2
            card_w = self._card_width()
            base_img_size = 135

            for offset in range(-3, 4):
                i = int(round(self._index)) + offset
                player = self._get_player(i)
                pixmap = self._get_pixmap_at(i)
                if player is None or pixmap is None:
                    continue

                dist = abs(offset - (self._index - round(self._index)))
                scale = max(0.5, 1.0 - (dist * 0.18))
                img_size = int(base_img_size * scale)
                cx = int(center_x + offset * card_w)

                opacity = 1.0
                if self._frozen:
                    opacity = 1.0 if self._selected == player else 0.35

                painter.setOpacity(opacity)

                px = pixmap.scaled(
                    img_size, img_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_x = cx - img_size // 2
                img_y = (base_img_size - img_size) // 2
                painter.drawPixmap(img_x, img_y, px)

                if self._selected == player and len(self._players) == 1:
                    painter.setOpacity(1.0)
                    pen = QPen(QColor("#FFFFFF"), 3)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(img_x, img_y, img_size, img_size)

        finally:
            painter.end()

    def set_players(self, players):
        if players is self._all_players or players == self._all_players:
            self._players = self._all_players
            self._pixmaps = self._all_pixmaps
        else:
            self._players = players
            self._pixmaps = [self._get_pixmap(p["name"]) for p in players]
        self._target_index = 0
        self._index = 0.0
        self._on_hover(self._players[0] if self._players else None)
        self.update()

    def _get_player(self, i):
        if len(self._players) <= 7:
            return None if i < 0 or i >= len(self._players) else self._players[i]
        return self._players[i % len(self._players)]

    def _get_pixmap_at(self, i):
        if len(self._players) <= 7:
            return None if i < 0 or i >= len(self._players) else self._pixmaps[i]
        return self._pixmaps[i % len(self._players)]

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QPixmap

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(280, 200)
        self.setStyleSheet("background: #10194D; color: white;")

        SoundManager.play("button")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._build_slider(
            str(ResourcePath.ICONS / "bgm.svg"),
            int(SoundManager.get_bgm_volume() * 100),
            lambda v: SoundManager.set_bgm_volume(v / 100)
        ))
        layout.addWidget(self._build_slider(
            str(ResourcePath.ICONS / "effects.svg"),
            int(SoundManager.get_effects_volume() * 100),
            lambda v: SoundManager.set_effects_volume(v / 100)
        ))

        ver_label = QLabel(f"Version {Session.VERSION}")
        ver_label.setStyleSheet("color:#999; font-size:14px;")
        layout.addWidget(ver_label, alignment=(Qt.AlignmentFlag.AlignCenter))

    def _build_slider(self, icon_path, value, on_change):
        container = QWidget()
        layout = QHBoxLayout(container)

        icon = QLabel()
        pixmap = QPixmap(icon_path)
        icon.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(value)
        slider.valueChanged.connect(on_change)

        layout.addWidget(icon)
        layout.addWidget(slider)

        return container
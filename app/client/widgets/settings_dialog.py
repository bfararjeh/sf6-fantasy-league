import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QColor

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.session import Session
from app.client.controllers.sound_manager import SoundManager


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(280, 240)
        self.setStyleSheet("background: #10194D; color: white;")

        SoundManager.play("button")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._build_slider(
            str(ResourcePath.ICONS / "bgm.svg"),
            int(SoundManager.get_bgm_volume() * 100),
            lambda v: (SoundManager.set_bgm_volume(v / 100), SoundManager.save_settings())
        ))
        layout.addWidget(self._build_slider(
            str(ResourcePath.ICONS / "effects.svg"),
            int(SoundManager.get_effects_volume() * 100),
            lambda v: (SoundManager.set_effects_volume(v / 100), SoundManager.save_settings())
        ))

        btn_cont = QWidget()
        btn_lay = QHBoxLayout(btn_cont)

        faqs_button = QPushButton("FAQs")
        faqs_button.setCursor(Qt.CursorShape.PointingHandCursor)
        faqs_button.setStyleSheet("color:#999; font-size:14px; background: transparent; border: none; text-decoration: underline;")
        faqs_button.clicked.connect(lambda: webbrowser.open(
            "https://github.com/bfararjeh/sf6-fantasy-league/blob/main/README.md#faqs"
        ))
        btn_lay.addWidget(faqs_button, alignment=Qt.AlignmentFlag.AlignCenter)

        credits_button = QPushButton("Credits")
        credits_button.setCursor(Qt.CursorShape.PointingHandCursor)
        credits_button.setStyleSheet("color:#999; font-size:14px; background: transparent; border: none; text-decoration: underline;")
        credits_button.clicked.connect(self._view_credits)
        btn_lay.addWidget(credits_button, alignment=Qt.AlignmentFlag.AlignCenter)

        ver_label = QLabel(f"Version {Session.VERSION}")
        ver_label.setStyleSheet("color:#999; font-size:14px;")
        layout.addWidget(btn_cont)
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

    def _view_credits(self):
        SoundManager.play("button")

        dialog = QDialog(self)
        dialog.setWindowTitle("Credits")
        dialog.setStyleSheet("background: #10194D; color: white;")
        dialog.setFixedSize(800, 600)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("Credits")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 28px; color: white;")
        layout.addWidget(title)

        with open(str(ResourcePath.TEXTS / "credits.txt"), "r") as file:
            text_list = file.read().splitlines()

        # Bio text for each person
        bios = {
            "fararjeh": text_list[0],
            "nabil": text_list[1],
        }

        # Text label (shared, switches on image click)
        bio_label = QLabel(bios["fararjeh"])
        bio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bio_label.setWordWrap(True)
        bio_label.setStyleSheet("font-size: 16px; color: white; padding: 10px;")

        # Image row
        image_cont = QWidget()
        image_row = QHBoxLayout(image_cont)
        image_row.setSpacing(40)
        image_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def make_glow_effect(active):
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(30 if active else 0)
            effect.setOffset(0, 0)
            effect.setColor(QColor(123, 156, 255, 220 if active else 0))
            return effect

        def make_image_card(image_path, label_text):
            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wrapper.setCursor(Qt.CursorShape.PointingHandCursor)
            col = QVBoxLayout(wrapper)
            col.setSpacing(6)
            col.setContentsMargins(0, 0, 0, 0)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            img_label = QLabel()
            img_label.setStyleSheet("background: transparent;")
            pixmap = QPixmap(image_path)
            img_label.setPixmap(pixmap.scaled(
                220, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setGraphicsEffect(make_glow_effect(False))

            name_label = QLabel(label_text)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("font-size: 18px; color: #aaa; background: transparent;")

            col.addWidget(img_label)
            col.addWidget(name_label)

            return wrapper, img_label

        fararjeh_wrapper, fararjeh_img = make_image_card(
            str(ResourcePath.IMAGES / "fararjeh.png"), "Fararjeh - Developer"
        )
        nabil_wrapper, nabil_img = make_image_card(
            str(ResourcePath.IMAGES / "nabil.png"), "Nabil - Chief Creative Officer"
        )

        def select(key, active_img, inactive_img):
            bio_label.setText(bios[key])
            active_img.setGraphicsEffect(make_glow_effect(True))
            inactive_img.setGraphicsEffect(make_glow_effect(False))

        fararjeh_wrapper.mousePressEvent = lambda _: select("fararjeh", fararjeh_img, nabil_img)
        nabil_wrapper.mousePressEvent    = lambda _: select("nabil",    nabil_img,    fararjeh_img)

        # Start with fararjeh selected
        fararjeh_img.setGraphicsEffect(make_glow_effect(True))

        image_row.addWidget(fararjeh_wrapper)
        image_row.addWidget(nabil_wrapper)

        layout.addWidget(image_cont)
        layout.addStretch()
        layout.addWidget(bio_label, stretch=1)
        layout.addStretch()

        dialog.exec()


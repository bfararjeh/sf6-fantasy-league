from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

from app.client.controllers.resource_path import ResourcePath


class SoundManager:
    _effects = {}

    @classmethod
    def init(cls):
        for name, filename in [
            ("click",   "click.wav"),
            ("success", "success.wav"),
            ("error",   "error.wav"),
            ("loaded",   "loaded.wav"),
            ("login",   "login.wav"),
            ("logout",   "logout.wav"),
            ("boot",   "boot.wav"),
        ]:
            path = str(ResourcePath.SOUNDS / filename)
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(0.5)
            cls._effects[name] = effect

    @classmethod
    def play(cls, name: str):
        if name in cls._effects:
            cls._effects[name].play()

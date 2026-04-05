import json
import os
from pathlib import Path

from PyQt6.QtMultimedia import QSoundEffect

from app.client.controllers.resource_path import ResourcePath

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl


class SoundManager:
    _effects = {}
    _player = None
    _audio_output = None
    _settings_filename = "sound_settings.json"

    @classmethod
    def init(cls):
        for name, filename in [
            ("success", "success.wav"),
            ("error",   "error.wav"),
            ("loaded",   "loaded.wav"),
            ("login",   "login.wav"),
            ("logout",   "logout.wav"),
            ("boot",   "boot.wav"),
            ("button", "button.wav"),
            ("prompt", "prompt.wav")
        ]:
            path = str(ResourcePath.SOUNDS / filename)
            cls._effect_output = QSoundEffect()
            cls._effect_output.setSource(QUrl.fromLocalFile(path))
            cls._effect_output.setVolume(0.5)
            cls._effects[name] = cls._effect_output

        cls._audio_output = QAudioOutput()
        cls._audio_output.setVolume(0.5)
        cls._player = QMediaPlayer()
        cls._player.setAudioOutput(cls._audio_output)
        cls._player.setSource(QUrl.fromLocalFile(str(ResourcePath.SOUNDS / "bgm.mp3")))
        cls._player.mediaStatusChanged.connect(cls._on_media_status)
        cls._player.play()

    @classmethod
    def play(cls, name: str):
        if name in cls._effects:
            cls._effects[name].play()

    @classmethod
    def _on_media_status(cls, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            cls._player.setPosition(0)
            cls._player.play()

    @classmethod
    def set_bgm_volume(cls, volume: float):
        if cls._audio_output:
            cls._audio_output.setVolume(volume)

    @classmethod
    def set_effects_volume(cls, volume: float):
        for effect in cls._effects.values():
            effect.setVolume(volume)

    @classmethod
    def get_bgm_volume(cls) -> float:
        return cls._audio_output.volume() if cls._audio_output else 0.5

    @classmethod
    def get_effects_volume(cls) -> float:
        effect = next(iter(cls._effects.values()), None)
        return effect.volume() if effect else 0.5

    @classmethod
    def _settings_path(cls) -> Path:
        if os.name == "nt":
            base = Path(os.environ["APPDATA"]) / "FantasySF6"
        else:
            base = Path.home() / ".config" / "FantasySF6"  # fallback for non-Windows
        base.mkdir(parents=True, exist_ok=True)
        return base / cls._settings_filename

    @classmethod
    def load_settings(cls):
        path = cls._settings_path()
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                cls.set_bgm_volume(data.get("bgm_volume", 1.0))
                cls.set_effects_volume(data.get("effects_volume", 1.0))
            except (json.JSONDecodeError, KeyError):
                pass  # Corrupt file — just use defaults

    @classmethod
    def save_settings(cls):
        path = cls._settings_path()
        with open(path, "w") as f:
            json.dump({
                "bgm_volume": cls.get_bgm_volume(),
                "effects_volume": cls.get_effects_volume()
            }, f)

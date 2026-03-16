from pathlib import Path
import sys


class ResourcePath:
    @staticmethod
    def resource_path(relative_path: str) -> Path:
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / relative_path
        return Path(relative_path).resolve()

    FLAGS = resource_path.__func__("app/client/assets/icons/flags")
    FONTS = resource_path.__func__("app/client/assets/fonts")
    ICONS = resource_path.__func__("app/client/assets/icons")
    IMAGES = resource_path.__func__("app/client/assets/images")
    PLAYERS = resource_path.__func__("app/client/assets/players")
    SOUNDS = resource_path.__func__("app/client/assets/sounds")
    
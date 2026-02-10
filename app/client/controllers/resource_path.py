
from pathlib import Path
import sys


class ResourcePath:
    @staticmethod
    def resource_path(relative_path: str) -> Path:
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / relative_path
        return Path(relative_path).resolve()

    AVATAR = resource_path.__func__("app/client/assets/avatars")
    PLAYERS = resource_path.__func__("app/client/assets/player_pictures")
    FLAGS = resource_path.__func__("app/client/assets/icons/flags")
    ICONS = resource_path.__func__("app/client/assets/icons")
    FONTS = resource_path.__func__("app/client/assets/fonts")
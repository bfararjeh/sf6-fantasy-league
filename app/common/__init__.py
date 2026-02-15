import sys
import os

from pathlib import Path

APP_NAME = "SF6FantasyLeague"


def get_app_data_dir() -> Path:
    if sys.platform == "win32":
        if "APPDATA" in os.environ:
            return Path(os.environ["APPDATA"]) / APP_NAME
        else:
            return Path.home() / "AppData" / "Roaming" / APP_NAME
    elif sys.platform == "linux":
        if "XDG_DATA_HOME" in os.environ:
            return Path(os.environ["XDG_DATA_HOME"]) / APP_NAME
        else:
            return Path.home() / ".local" / "share" / APP_NAME

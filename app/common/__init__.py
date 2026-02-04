import sys
import os

from pathlib import Path

APP_NAME = "SF6FantasyLeague"


def get_app_data_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / APP_NAME
    elif sys.platform == "linux":
        return Path(os.environ["XDG_DATA_HOME"]) / APP_NAME

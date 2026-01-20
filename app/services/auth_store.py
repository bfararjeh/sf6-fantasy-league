import json
import os
from pathlib import Path

def get_app_data_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "SF6FantasyLeague"

class AuthStore:
    '''
    Methods for saving, loading, and clearing stored sessions. Nothing fancy,
    just json dumps and path grabbing using the os library.

    Method names are self explanatory.
    '''
    _filename = "session.json"

    @classmethod
    def _path(cls) -> Path:
        base = get_app_data_dir()
        base.mkdir(parents=True, exist_ok=True)
        return base / cls._filename

    @classmethod
    def save(cls, auth_data: dict):
        with open(cls._path(), "w", encoding="utf-8") as f:
            json.dump(auth_data, f)

    @classmethod
    def load(cls) -> dict | None:
        path = cls._path()
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def clear(cls):
        path = cls._path()
        if path.exists():
            path.unlink()
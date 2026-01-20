import json
import os

from pathlib import Path

from typing import Any

def get_app_data_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "SF6FantasyLeague"

class AppStore:
    '''
    Methods for saving, loading, and clearing local app data.

    Method names are self explanatory.
    '''
    _filename = "appdata.json"

    @classmethod
    def _path(cls) -> Path:
        base = get_app_data_dir()
        base.mkdir(parents=True, exist_ok=True)
        return base / cls._filename

    @classmethod
    def _load_all(cls) -> dict:
        path = cls._path()
        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def _save_all(cls, data: dict):
        with open(cls._path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---------- public API ----------

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Supports dotted access: "players_cache.data"
        """
        data = cls._load_all()
        current = data

        for part in key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part)
            if current is None:
                return default

        return current

    @classmethod
    def set(cls, key: str, value: Any):
        """
        Supports dotted access: "players_cache.data"
        """
        data = cls._load_all()
        current = data
        parts = key.split(".")

        for part in parts[:-1]:
            current = current.setdefault(part, {})

        current[parts[-1]] = value
        cls._save_all(data)

    @classmethod
    def delete(cls, key: str):
        data = cls._load_all()
        current = data
        parts = key.split(".")

        for part in parts[:-1]:
            current = current.get(part)
            if not isinstance(current, dict):
                return

        current.pop(parts[-1], None)
        cls._save_all(data)

    @classmethod
    def clear(cls):
        path = cls._path()
        if path.exists():
            path.unlink()
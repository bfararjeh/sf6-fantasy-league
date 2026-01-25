import json
import os

from pathlib import Path

from typing import Any

def get_app_data_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "SF6FantasyLeague"

class AppStore:
    """
    Simple local cache where every key maps to a list.
    """
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
    def get(cls, key: str) -> list:
        """
        Always returns a list.
        """
        data = cls._load_all()
        value = data.get(key, [])
        return value if isinstance(value, list) else []

    @classmethod
    def append(cls, key: str, value):
        """
        Appends value(s) to the list stored at key.
        """
        data = cls._load_all()

        if key not in data or not isinstance(data[key], list):
            data[key] = []

        if isinstance(value, list):
            data[key].extend(value)
        else:
            data[key].append(value)

        cls._save_all(data)

    @classmethod
    def remove(cls, key, value):
        data = cls._load_all()

        if key not in data:
            raise KeyError(f"Key '{key}' does not exist.")

        if not isinstance(data[key], list):
            raise TypeError(f"Value for '{key}' is not a list.")

        try:
            data[key].remove(value)
        except ValueError:
            raise ValueError(f"Value '{value}' not found in '{key}'.")

        cls._save_all(data)

    @classmethod
    def clear(cls):
        path = cls._path()
        if path.exists():
            path.unlink()
        path = cls._path()
        if path.exists():
            path.unlink()
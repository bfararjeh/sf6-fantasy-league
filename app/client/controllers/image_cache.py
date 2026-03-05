import json
from pathlib import Path
from typing import Optional
from app.client.controllers.resource_path import ResourcePath

class ImageCache:
    """
    Handles local disk caching of remote images with ETag-based invalidation.
    Falls back to baked-in assets, then placeholders.
    """

    _cache_dir: Path = None
    _index: dict = {}
    _index_path: Path = None

    PLACEHOLDERS = {
        "events":  str(ResourcePath.IMAGES / "event_placeholder.png"),
        "players":  str(ResourcePath.IMAGES / "uni_placeholder.png"),
        "avatars":   str(ResourcePath.IMAGES / "uni_placeholder.png"),
    }

    BAKED_DIRS = {
        "players": ResourcePath.PLAYERS,
    }

    @classmethod
    def init(cls, cache_dir: Path):
        cls._cache_dir = cache_dir
        cls._index_path = cache_dir / "index.json"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cls._load_index()

    @classmethod
    def _load_index(cls):
        if cls._index_path.exists():
            try:
                cls._index = json.loads(cls._index_path.read_text())
            except Exception:
                cls._index = {}
        else:
            cls._index = {}

    @classmethod
    def _save_index(cls):
        try:
            cls._index_path.write_text(json.dumps(cls._index, indent=2))
        except Exception:
            pass

    @classmethod
    def _cache_path(cls, image_type: str, key: str) -> Path:
        return cls._cache_dir / f"{image_type}_{key}.webp"

    @classmethod
    def _index_key(cls, image_type: str, key: str) -> str:
        return f"{image_type}:{key}"

    @classmethod
    def store(cls, image_type: str, key: str, data: bytes, etag: str):
        """Store image bytes and ETag to disk cache."""
        path = cls._cache_path(image_type, key)
        try:
            path.write_bytes(data)
            cls._index[cls._index_key(image_type, key)] = etag
            cls._save_index()
        except Exception:
            pass

    @classmethod
    def get_cached(cls, image_type: str, key: str) -> Optional[bytes]:
        """Return cached bytes if they exist on disk, else None."""
        path = cls._cache_path(image_type, key)
        if path.exists():
            try:
                return path.read_bytes()
            except Exception:
                return None
        return None

    @classmethod
    def get_etag(cls, image_type: str, key: str) -> Optional[str]:
        """Return stored ETag for a cached image."""
        return cls._index.get(cls._index_key(image_type, key))

    @classmethod
    def get_baked(cls, image_type: str, key: str) -> Optional[bytes]:
        """Return bytes from baked-in assets if available."""
        baked_dir = cls.BAKED_DIRS.get(image_type)
        if not baked_dir:
            return None
        for ext in (".jpg", ".png", ".webp"):
            path = baked_dir / f"{key}{ext}"
            if path.exists():
                try:
                    return path.read_bytes()
                except Exception:
                    return None
        return None

    @classmethod
    def get_placeholder(cls, image_type: str) -> Optional[bytes]:
        """Return placeholder bytes for the given image type."""
        path = cls.PLACEHOLDERS.get(image_type)
        if not path:
            return None
        try:
            return Path(path).read_bytes()
        except Exception:
            return None

    @classmethod
    def invalidate(cls, image_type: str, key: str):
        path = cls._cache_path(image_type, key)
        if path.exists():
            path.unlink()
        index_key = cls._index_key(image_type, key)
        if index_key in cls._index:
            del cls._index[index_key]
            cls._save_index()
"""User playlist library — multiple M3U / Xtream sources."""

import json
import uuid
from pathlib import Path

from tvwhere.config import CONFIG_DIR, PLAYLISTS, ensure_dirs

PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"


def _builtin_playlists() -> list:
    items = []
    for key, url in PLAYLISTS.items():
        items.append(
            {
                "id": f"builtin-{key.lower()}",
                "name": key,
                "type": "builtin",
                "url": url,
                "builtin_key": key,
            }
        )
    return items


class PlaylistManager:
    _cache = None

    @classmethod
    def invalidate(cls):
        cls._cache = None

    @classmethod
    def load_all(cls) -> list:
        if cls._cache is not None:
            return cls._cache
        ensure_dirs()
        user = []
        if PLAYLISTS_FILE.exists():
            try:
                with open(PLAYLISTS_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        user = data
            except Exception:
                pass
        cls._cache = _builtin_playlists() + user
        return cls._cache

    @classmethod
    def save_user(cls, playlists: list):
        ensure_dirs()
        cls._cache = _builtin_playlists() + playlists
        try:
            with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
                json.dump(playlists, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"Playlist save failed: {exc}")

    @classmethod
    def get(cls, playlist_id: str) -> dict:
        for pl in cls.load_all():
            if pl["id"] == playlist_id:
                return pl
        return None

    @classmethod
    def add_m3u(cls, name: str, url: str, epg_url: str = "") -> dict:
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": name.strip() or "M3U Playlist",
            "type": "m3u",
            "url": url.strip(),
            "epg_url": epg_url.strip(),
        }
        user = [p for p in cls.load_all() if not p["id"].startswith("builtin-")]
        user.append(entry)
        cls.save_user(user)
        return entry

    @classmethod
    def add_xtream(cls, name: str, server: str, username: str, password: str) -> dict:
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": name.strip() or "Xtream",
            "type": "xtream",
            "server": server.strip(),
            "username": username.strip(),
            "password": password.strip(),
        }
        user = [p for p in cls.load_all() if not p["id"].startswith("builtin-")]
        user.append(entry)
        cls.save_user(user)
        return entry

    @classmethod
    def add_file(cls, name: str, file_path: str) -> dict:
        src = Path(file_path).expanduser()
        if not src.is_file():
            raise FileNotFoundError("Playlist file not found.")
        dest_dir = CONFIG_DIR / "playlists"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{uuid.uuid4().hex[:8]}_{src.name}"
        dest.write_bytes(src.read_bytes())
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": name.strip() or src.stem,
            "type": "file",
            "url": str(dest),
        }
        user = [p for p in cls.load_all() if not p["id"].startswith("builtin-")]
        user.append(entry)
        cls.save_user(user)
        return entry

    @classmethod
    def remove(cls, playlist_id: str) -> bool:
        if playlist_id.startswith("builtin-"):
            return False
        user = [p for p in cls.load_all() if not p["id"].startswith("builtin-")]
        new_user = [p for p in user if p["id"] != playlist_id]
        if len(new_user) == len(user):
            return False
        cls.save_user(new_user)
        return True

    @classmethod
    def user_playlists(cls) -> list:
        return [p for p in cls.load_all() if not p["id"].startswith("builtin-")]

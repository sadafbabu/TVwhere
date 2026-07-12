"""Recently watched channels."""

import json
from datetime import datetime

from tvwhere.config import CONFIG_DIR, ensure_dirs
from tvwhere.models import channel_id

HISTORY_FILE = CONFIG_DIR / "history.json"
MAX_HISTORY = 50


class HistoryManager:
    _cache = None

    @classmethod
    def invalidate(cls):
        cls._cache = None

    @classmethod
    def load(cls) -> list:
        if cls._cache is not None:
            return cls._cache
        ensure_dirs()
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    cls._cache = data if isinstance(data, list) else []
                    return cls._cache
            except Exception:
                pass
        cls._cache = []
        return cls._cache

    @classmethod
    def save(cls, items: list):
        ensure_dirs()
        cls._cache = items
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"History save failed: {exc}")

    @classmethod
    def add(cls, channel: dict):
        cid = channel.get("id") or channel_id(channel.get("url", ""))
        entry = dict(channel)
        entry["id"] = cid
        entry["watched_at"] = datetime.utcnow().isoformat() + "Z"
        items = [e for e in cls.load() if e.get("id") != cid]
        items.insert(0, entry)
        cls.save(items[:MAX_HISTORY])

    @classmethod
    def get_all(cls) -> list:
        return list(cls.load())

    @classmethod
    def clear(cls):
        cls.save([])

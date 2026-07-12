import json
import os
import sys
import tkinter.font as tkfont
from pathlib import Path
from typing import Optional

HOME = Path.home()

if os.name == "nt":
    CONFIG_DIR = Path(os.environ.get("APPDATA", HOME)) / "tvwhere"
    CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", HOME)) / "tvwhere" / "cache"
else:
    CONFIG_DIR = HOME / ".config" / "tvwhere"
    CACHE_DIR = HOME / ".cache" / "tvwhere"

FAVORITES_FILE = CONFIG_DIR / "favorites.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

_PKG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PKG_DIR.parent

ICON_CANDIDATES = [
    _PROJECT_ROOT / "assets" / "icon.png",
    _PROJECT_ROOT / "assets" / "icon-256.png",
    _PROJECT_ROOT / "assets" / "icon-48.png",
    _PKG_DIR / "assets" / "icon.png",
]


def resolve_icon_path() -> Optional[Path]:
    for path in ICON_CANDIDATES:
        if path.is_file():
            return path
    return None


ICON_PATH = resolve_icon_path()

PLAYLISTS = {
    "Bangladesh": "https://iptv-org.github.io/iptv/countries/bd.m3u",
    "Bengali": "https://iptv-org.github.io/iptv/languages/ben.m3u",
    "Global": "https://iptv-org.github.io/iptv/index.m3u",
}

SIDEBAR_TABS = [
    "Bangladesh",
    "Bengali",
    "Global",
    "Favorites",
    "Recent",
    "Custom URL",
]

DEFAULT_TAB = "Bangladesh"

THEME = {
    "bg": "#0a0a0a",
    "bg_secondary": "#141414",
    "bg_card": "#1a1a1a",
    "bg_hover": "#262626",
    "bg_active": "#303030",
    "fg": "#e8e8e8",
    "fg_dim": "#7a7a7a",
    "fg_accent": "#c8c8c8",
    "border": "#2a2a2a",
    "search_bg": "#121212",
    "scrollbar": "#1e1e1e",
    "scrollbar_active": "#3a3a3a",
    "badge_bg": "#2a2a2a",
    "badge_fg": "#9a9a9a",
    "empty_fg": "#5a5a5a",
    "error_fg": "#e07070",
}

CACHE_TTL = 3600
PAGE_SIZE = 80
SEARCH_DEBOUNCE_MS = 150


def _font_family() -> str:
    if sys.platform == "win32":
        return "Segoe UI"
    if sys.platform == "darwin":
        return "Helvetica Neue"
    try:
        return tkfont.nametofont("TkDefaultFont").actual()["family"]
    except Exception:
        return "TkDefaultFont"


_FONT = _font_family()

FONTS = {
    "title": (_FONT, 16, "bold"),
    "heading": (_FONT, 11),
    "body": (_FONT, 10),
    "small": (_FONT, 9),
    "search": (_FONT, 11),
}


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


class SettingsManager:
    _cache = None

    @classmethod
    def load(cls) -> dict:
        if cls._cache is not None:
            return cls._cache
        ensure_dirs()
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    cls._cache = data if isinstance(data, dict) else {}
                    return cls._cache
            except Exception:
                pass
        cls._cache = {}
        return cls._cache

    @classmethod
    def save(cls, data: dict):
        ensure_dirs()
        cls._cache = data
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            print(f"Settings save failed: {exc}")

    @classmethod
    def get_last_tab(cls) -> str:
        tab = cls.load().get("last_tab", DEFAULT_TAB)
        return tab if tab in SIDEBAR_TABS and tab != "Custom URL" else DEFAULT_TAB

    @classmethod
    def set_last_tab(cls, tab: str):
        if tab == "Custom URL":
            return
        data = dict(cls.load())
        data["last_tab"] = tab
        cls.save(data)


class FavoritesManager:
    _cache = None

    @classmethod
    def invalidate(cls):
        cls._cache = None

    @classmethod
    def load(cls) -> dict:
        if cls._cache is not None:
            return cls._cache
        ensure_dirs()
        if FAVORITES_FILE.exists():
            try:
                with open(FAVORITES_FILE, encoding="utf-8") as f:
                    cls._cache = json.load(f)
                    return cls._cache
            except Exception:
                pass
        cls._cache = {}
        return cls._cache

    @classmethod
    def save(cls, favorites: dict):
        ensure_dirs()
        cls._cache = favorites
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(favorites, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"Favorites save failed: {exc}")

    @classmethod
    def add(cls, name: str, url: str, group: str = "General", logo: str = ""):
        favs = dict(cls.load())
        favs[name] = {"name": name, "url": url, "group": group, "logo": logo}
        cls.save(favs)

    @classmethod
    def remove(cls, name: str):
        favs = dict(cls.load())
        if name in favs:
            del favs[name]
            cls.save(favs)

    @classmethod
    def is_favorite(cls, name: str) -> bool:
        return name in cls.load()

    @classmethod
    def get_all(cls) -> list:
        return list(cls.load().values())

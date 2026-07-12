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

# Legacy — country filter replaces per-country sidebar tabs
PLAYLISTS = {}

SIDEBAR_TABS = [
    "Favorites",
    "Recent",
    "Custom URL",
]

DEFAULT_TAB = "channels"
DEFAULT_COUNTRY = "global"

CACHE_TTL = 3600
PAGE_SIZE = 80
SEARCH_DEBOUNCE_MS = 180
AUTO_REFRESH_MINUTES = 45

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
        if tab in SIDEBAR_TABS:
            return tab
        legacy = {"Live TV", "Bangladesh", "Bengali", "Global", "channels"}
        if tab in legacy:
            return DEFAULT_TAB
        return DEFAULT_TAB

    @classmethod
    def set_last_tab(cls, tab: str):
        data = dict(cls.load())
        if tab == "channels":
            data["last_tab"] = DEFAULT_TAB
        elif tab in SIDEBAR_TABS:
            data["last_tab"] = tab
        else:
            return
        cls.save(data)

    @classmethod
    def get_country(cls) -> str:
        from tvwhere.countries import DEFAULT_COUNTRY as DC, is_valid_code

        code = cls.load().get("country", DEFAULT_COUNTRY)
        return code if is_valid_code(code) else DC

    @classmethod
    def set_country(cls, code: str):
        data = dict(cls.load())
        data["country"] = code
        cls.save(data)

    @classmethod
    def hide_dead_channels(cls) -> bool:
        return cls.load().get("hide_dead", True)

    @classmethod
    def set_hide_dead(cls, value: bool):
        data = dict(cls.load())
        data["hide_dead"] = value
        cls.save(data)

    @classmethod
    def show_unavailable(cls) -> bool:
        return cls.load().get("show_unavailable", False)

    @classmethod
    def set_show_unavailable(cls, value: bool):
        data = dict(cls.load())
        data["show_unavailable"] = value
        cls.save(data)

    @classmethod
    def get_resolution(cls) -> str:
        return cls.load().get("resolution", "")

    @classmethod
    def set_resolution(cls, value: str):
        data = dict(cls.load())
        data["resolution"] = value
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

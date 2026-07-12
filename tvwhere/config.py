import os
import json
from pathlib import Path

# Base Directories
HOME = Path.home()
if os.name == 'nt':  # Windows
    CONFIG_DIR = Path(os.environ.get('APPDATA', HOME)) / 'tvwhere'
    CACHE_DIR = Path(os.environ.get('LOCALAPPDATA', HOME)) / 'tvwhere' / 'Cache'
else:  # Linux / macOS
    CONFIG_DIR = HOME / '.config' / 'tvwhere'
    CACHE_DIR = HOME / '.cache' / 'tvwhere'

FAVORITES_FILE = CONFIG_DIR / 'favorites.json'
SETTINGS_FILE = CONFIG_DIR / 'settings.json'

# M3U Playlists from iptv-org
PLAYLISTS = {
    'Bangladesh': 'https://iptv-org.github.io/iptv/countries/bd.m3u',
    'Bengali': 'https://iptv-org.github.io/iptv/languages/ben.m3u',
    'Global': 'https://iptv-org.github.io/iptv/index.m3u'
}

# Minimalist Dark Grey/Black Theme
THEME = {
    'bg': '#121212',            # Deep black
    'bg_secondary': '#1a1a1a',  # Dark grey sidebar/titlebar
    'bg_card': '#222222',       # Channel list items
    'bg_hover': '#2d2d2d',      # Hover state
    'bg_active': '#333333',     # Selected state
    'fg': '#e5e5e5',            # High contrast text
    'fg_dim': '#9e9e9e',        # Low contrast text
    'fg_accent': '#906cf2',     # Premium purple accent
    'border': '#2d2d2d',        # Borders
    'search_bg': '#1e1e1e',     # Search bar bg
    'scrollbar': '#2d2d2d',     # Scrollbar trough
    'scrollbar_active': '#444444', # Scrollbar handle
    'badge_bg': '#333333',      # Group badges
}

# Typography
FONTS = {
    'title': ('Noto Sans', 14, 'bold'),
    'heading': ('Noto Sans', 11, 'bold'),
    'body': ('Noto Sans', 10),
    'small': ('Noto Sans', 8),
    'search': ('Noto Sans', 11)
}

CACHE_TTL = 3600  # 1 hour cache validity

def ensure_dirs():
    """Ensure that config and cache directories exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

class FavoritesManager:
    """Manages favorited channels saved to local JSON."""
    @staticmethod
    def load() -> dict:
        ensure_dirs()
        if FAVORITES_FILE.exists():
            try:
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def save(favorites: dict):
        ensure_dirs()
        try:
            with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    @classmethod
    def add(cls, name: str, url: str, group: str = "General", logo: str = ""):
        favs = cls.load()
        favs[name] = {
            'name': name,
            'url': url,
            'group': group,
            'logo': logo
        }
        cls.save(favs)

    @classmethod
    def remove(cls, name: str):
        favs = cls.load()
        if name in favs:
            del favs[name]
            cls.save(favs)

    @classmethod
    def is_favorite(cls, name: str) -> bool:
        favs = cls.load()
        return name in favs

    @classmethod
    def get_all(cls) -> list:
        favs = cls.load()
        return list(favs.values())

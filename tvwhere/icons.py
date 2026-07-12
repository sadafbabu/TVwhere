"""Cross-platform icon loading for TVwhere."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

_PKG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PKG_DIR.parent
_ASSETS = _PROJECT_ROOT / "assets"


def _asset(name: str) -> Optional[Path]:
    path = _ASSETS / name
    return path if path.is_file() else None


def primary_icon_path() -> Optional[Path]:
    for name in ("icon.png", "icon-256.png"):
        path = _asset(name)
        if path:
            return path
    svg = _asset("icon.svg")
    if svg:
        return svg
    return None


def _load_photo(path: Path, size: int = 0) -> Optional[tk.PhotoImage]:
    try:
        image = tk.PhotoImage(file=str(path))
        if size and image.width() > size:
            factor = max(1, round(image.width() / size))
            image = image.subsample(factor, factor)
        return image
    except Exception:
        return None


def apply_window_icon(root: tk.Tk) -> Optional[tk.PhotoImage]:
    path = primary_icon_path()
    if not path or path.suffix == ".svg":
        return None
    image = _load_photo(path)
    if image:
        root.iconphoto(True, image)
    return image


def load_logo(size: int = 28) -> Optional[tk.PhotoImage]:
    path = primary_icon_path()
    if not path or path.suffix == ".svg":
        return None
    return _load_photo(path, size=size)

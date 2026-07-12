"""Resolution detection and filtering."""

import re

RESOLUTION_ORDER = ("4K", "1080p", "720p", "SD")

FILTER_OPTIONS = [
    ("", "All qualities"),
    ("4K", "4K / UHD"),
    ("1080p", "1080p"),
    ("720p", "720p"),
    ("SD", "SD"),
]

_PATTERNS = [
    (re.compile(r"\b(4k|2160p|uhd|ultra\s*hd)\b", re.I), "4K"),
    (re.compile(r"\b1080p?\b", re.I), "1080p"),
    (re.compile(r"\b720p?\b", re.I), "720p"),
    (re.compile(r"\b(480p|360p|240p|sd)\b", re.I), "SD"),
]


def detect_resolution(name: str = "", group: str = "", extra: str = "") -> str:
    blob = f"{name} {group} {extra}"
    for pattern, label in _PATTERNS:
        if pattern.search(blob):
            return label
    return ""


def normalize_resolution(value: str) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    if v in ("4k", "2160p", "uhd"):
        return "4K"
    if v in ("1080p", "1080", "fhd"):
        return "1080p"
    if v in ("720p", "720", "hd"):
        return "720p"
    if v in ("480p", "360p", "240p", "sd"):
        return "SD"
    return value


def channel_resolution(channel: dict) -> str:
    res = normalize_resolution(channel.get("resolution", ""))
    if res:
        return res
    return detect_resolution(
        channel.get("name", ""),
        channel.get("group", ""),
    )


def filter_by_resolution(channels: list, resolution: str) -> list:
    if not resolution or resolution == "All":
        return channels
    want = normalize_resolution(resolution)
    if not want:
        return channels
    return [ch for ch in channels if channel_resolution(ch) == want]

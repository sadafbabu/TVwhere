"""Channel search helpers — normalized, multi-word matching."""

import re
import unicodedata


def normalize(text: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _channel_blob(channel: dict) -> str:
    parts = [
        channel.get("name", ""),
        channel.get("group", ""),
        channel.get("resolution", ""),
    ]
    return normalize(" ".join(parts))


def filter_channels(channels: list, query: str) -> list:
    """Return channels matching every whitespace-separated search token."""
    normalized = normalize(query)
    if not normalized:
        return list(channels)

    tokens = normalized.split()
    return [ch for ch in channels if all(t in _channel_blob(ch) for t in tokens)]

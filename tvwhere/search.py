"""Channel search — normalized multi-word matching with relevance ranking."""

import re
import unicodedata


def normalize(text: str) -> str:
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


def _score(channel: dict, tokens: list) -> int:
    name = normalize(channel.get("name", ""))
    group = normalize(channel.get("group", ""))
    blob = _channel_blob(channel)
    score = 0
    for token in tokens:
        if token in name:
            if name.startswith(token):
                score += 30
            else:
                score += 20
        elif token in group:
            score += 8
        elif token in blob:
            score += 3
    return score


def filter_channels(channels: list, query: str) -> list:
    normalized = normalize(query)
    if not normalized:
        return list(channels)

    tokens = normalized.split()
    matched = []
    for ch in channels:
        blob = _channel_blob(ch)
        if all(t in blob for t in tokens):
            matched.append((_score(ch, tokens), ch))

    matched.sort(key=lambda item: (-item[0], normalize(item[1].get("name", ""))))
    return [ch for _, ch in matched]


def sort_channels(channels: list) -> list:
    return sorted(channels, key=lambda ch: normalize(ch.get("name", "")))

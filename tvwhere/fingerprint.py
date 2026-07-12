"""Playlist fingerprinting for silent refresh."""

import hashlib


def channels_fingerprint(channels: list) -> str:
    if not channels:
        return ""
    parts = sorted(f"{c.get('url', '')}|{c.get('name', '')}" for c in channels)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]

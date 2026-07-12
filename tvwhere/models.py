"""Shared data models for TVwhere."""

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


def channel_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


@dataclass
class Channel:
    name: str
    url: str
    group: str = "General"
    logo: str = ""
    resolution: str = ""
    tvg_id: str = ""
    playlist_id: str = ""

    @property
    def id(self) -> str:
        return channel_id(self.url)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        return cls(
            name=data.get("name", "Unknown"),
            url=data.get("url", ""),
            group=data.get("group", "General"),
            logo=data.get("logo", ""),
            resolution=data.get("resolution", ""),
            tvg_id=data.get("tvg_id", ""),
            playlist_id=data.get("playlist_id", ""),
        )


@dataclass
class Playlist:
    id: str
    name: str
    type: str  # builtin | m3u | xtream | file
    url: str = ""
    server: str = ""
    username: str = ""
    password: str = ""
    epg_url: str = ""
    builtin_key: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Playlist":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Playlist"),
            type=data.get("type", "m3u"),
            url=data.get("url", ""),
            server=data.get("server", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            epg_url=data.get("epg_url", ""),
            builtin_key=data.get("builtin_key", ""),
        )


@dataclass
class EpgProgram:
    channel_id: str
    title: str
    start: str
    stop: str
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

"""Central service layer — shared by desktop and web API."""

import threading
from pathlib import Path
from typing import Callable, Optional

from tvwhere.epg import fetch_epg_xml, match_channel_epg, parse_channel_names, parse_programs
from tvwhere.history import HistoryManager
from tvwhere.iptv import (
    clear_playlist_cache,
    get_cached_playlist,
    parse_m3u,
    save_to_cache,
)
from tvwhere.models import Channel, channel_id
from tvwhere.playlists import PlaylistManager
from tvwhere.search import filter_channels, sort_channels
from tvwhere.xtream import get_live_streams, validate_login, xtream_error_message


class PlaylistService:
    """Load and cache channels for any playlist type."""

    _locks = {}

    @classmethod
    def list_playlists(cls) -> list:
        return PlaylistManager.load_all()

    @classmethod
    def get_groups(cls, channels: list) -> list:
        groups = {}
        for ch in channels:
            g = ch.get("group") or "General"
            groups[g] = groups.get(g, 0) + 1
        return [{"name": k, "count": v} for k, v in sorted(groups.items(), key=lambda x: x[0].lower())]

    @classmethod
    def load_channels_sync(cls, playlist_id: str, force: bool = False) -> list:
        pl = PlaylistManager.get(playlist_id)
        if not pl:
            raise ValueError("Playlist not found.")

        if pl["type"] in ("builtin", "m3u"):
            url = pl["url"]
            return cls._fetch_m3u_sync(url, playlist_id, force)

        if pl["type"] == "xtream":
            try:
                validate_login(pl["server"], pl["username"], pl["password"])
                channels = get_live_streams(
                    pl["server"], pl["username"], pl["password"], playlist_id
                )
                return sort_channels(channels)
            except Exception as exc:
                raise ValueError(xtream_error_message(exc)) from exc

        if pl["type"] == "file":
            path = Path(pl["url"])
            if not path.is_file():
                raise ValueError("Playlist file not found.")
            content = path.read_text(encoding="utf-8", errors="ignore")
            channels = parse_m3u(content)
            return cls._tag_channels(sort_channels(channels), playlist_id)

        raise ValueError(f"Unsupported playlist type: {pl['type']}")

    @classmethod
    def _fetch_m3u_sync(cls, url: str, playlist_id: str, force: bool) -> list:
        if force:
            clear_playlist_cache(url)
        if not force:
            cached = get_cached_playlist(url)
            if cached:
                return cls._tag_channels(sort_channels(cached), playlist_id)
            stale = get_cached_playlist(url, allow_stale=True)
            if stale:
                return cls._tag_channels(sort_channels(stale), playlist_id)

        import urllib.request

        from tvwhere.iptv import USER_AGENT

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=25) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        channels = parse_m3u(content)
        if not channels:
            stale = get_cached_playlist(url, allow_stale=True)
            if stale:
                return cls._tag_channels(sort_channels(stale), playlist_id)
            raise ValueError("Playlist is empty or could not be parsed.")
        save_to_cache(url, channels)
        return cls._tag_channels(sort_channels(channels), playlist_id)

    @classmethod
    def _tag_channels(cls, channels: list, playlist_id: str) -> list:
        tagged = []
        for ch in channels:
            item = dict(ch)
            item["playlist_id"] = playlist_id
            item["id"] = channel_id(item.get("url", ""))
            tagged.append(item)
        return tagged

    @classmethod
    def load_channels_async(
        cls,
        playlist_id: str,
        on_ok: Callable,
        on_err: Callable,
        force: bool = False,
    ):
        def worker():
            try:
                channels = cls.load_channels_sync(playlist_id, force=force)
                on_ok(channels)
            except Exception as exc:
                on_err(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    @classmethod
    def search(cls, channels: list, query: str, group: Optional[str] = None) -> list:
        result = channels
        if group and group != "All":
            result = [c for c in result if (c.get("group") or "General") == group]
        if query.strip():
            result = filter_channels(result, query)
        return result

    @classmethod
    def get_epg_for_channel(cls, channel: dict, playlist: dict) -> dict:
        epg_url = playlist.get("epg_url", "")
        if not epg_url:
            return {"now": None, "next": None}
        try:
            xml = fetch_epg_xml(epg_url)
            programs = parse_programs(xml)
            names = parse_channel_names(xml)
            return match_channel_epg(channel, programs, names)
        except Exception:
            return {"now": None, "next": None}

    @classmethod
    def record_play(cls, channel: dict):
        HistoryManager.add(channel)

    @classmethod
    def favorites_key(cls, channel: dict) -> str:
        return channel.get("id") or channel_id(channel.get("url", ""))

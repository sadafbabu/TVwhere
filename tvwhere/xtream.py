"""Xtream Codes API — inspired by open IPTV players (IPTVnator, Fred TV patterns)."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

from typing import Any

from tvwhere.iptv import USER_AGENT
from tvwhere.models import Channel

_RES_RE = re.compile(r"\b(4k|2160p|1080p|720p|480p|360p)\b", re.I)


def _normalize_server(server: str) -> str:
    server = server.strip().rstrip("/")
    if not server.startswith(("http://", "https://")):
        server = "http://" + server
    return server


def _api_url(server: str, username: str, password: str, action: str) -> str:
    base = _normalize_server(server)
    params = urllib.parse.urlencode(
        {"username": username, "password": password, "action": action}
    )
    return f"{base}/player_api.php?{params}"


def _fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def validate_login(server: str, username: str, password: str) -> dict:
    url = _api_url(server, username, password, "get_account_info")
    data = _fetch_json(url)
    if not isinstance(data, dict) or "user_info" not in data:
        raise ValueError("Invalid Xtream credentials or server.")
    return data


def get_live_streams(server: str, username: str, password: str, playlist_id: str = "") -> list:
    base = _normalize_server(server)
    url = _api_url(server, username, password, "get_live_streams")
    streams = _fetch_json(url)
    if not isinstance(streams, list):
        raise ValueError("Could not load live streams from Xtream API.")

    categories = {}
    try:
        cat_url = _api_url(server, username, password, "get_live_categories")
        cats = _fetch_json(cat_url)
        if isinstance(cats, list):
            categories = {str(c.get("category_id")): c.get("category_name", "General") for c in cats}
    except Exception:
        pass

    channels = []
    seen = set()
    for item in streams:
        stream_id = item.get("stream_id") or item.get("num")
        if stream_id is None:
            continue
        name = (item.get("name") or f"Channel {stream_id}").strip()
        cat_id = str(item.get("category_id", ""))
        group = categories.get(cat_id, item.get("category_name") or "Live TV")
        logo = item.get("stream_icon") or ""
        stream_url = f"{base}/live/{username}/{password}/{stream_id}.m3u8"
        if stream_url in seen:
            continue
        seen.add(stream_url)
        res_match = _RES_RE.search(name)
        channels.append(
            Channel(
                name=name,
                url=stream_url,
                group=group,
                logo=logo,
                resolution=res_match.group(1).lower() if res_match else "",
                tvg_id=str(item.get("epg_channel_id") or ""),
                playlist_id=playlist_id,
            ).to_dict()
        )
    return channels


def xtream_error_message(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"Xtream HTTP {exc.code}: check server URL and credentials."
    if isinstance(exc, urllib.error.URLError):
        return f"Xtream network error: {exc.reason}"
    return str(exc)

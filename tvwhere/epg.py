"""XMLTV EPG parser — basic now/next support."""

import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from tvwhere.config import CACHE_DIR, ensure_dirs
from tvwhere.iptv import USER_AGENT, get_url_hash

_EPG_TTL = 7200


def _epg_cache_path(url: str):
    return CACHE_DIR / f"epg_{get_url_hash(url)}.xml"


def fetch_epg_xml(url: str, force: bool = False) -> str:
    ensure_dirs()
    path = _epg_cache_path(url)
    if not force and path.exists():
        age = time.time() - path.stat().st_mtime
        if age < _EPG_TTL:
            return path.read_text(encoding="utf-8", errors="ignore")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    path.write_text(content, encoding="utf-8")
    return content


def _parse_xmltv_time(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y%m%d%H%M%S %z", "%Y%m%d%H%M%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def parse_programs(xml_text: str) -> dict:
    """Return {channel_xml_id: [programs sorted by start]}."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}

    by_channel = {}
    for prog in root.findall("programme"):
        ch = prog.get("channel", "")
        if not ch:
            continue
        title_el = prog.find("title")
        desc_el = prog.find("desc")
        entry = {
            "title": (title_el.text or "").strip() if title_el is not None else "",
            "description": (desc_el.text or "").strip() if desc_el is not None else "",
            "start": prog.get("start", ""),
            "stop": prog.get("stop", ""),
            "start_dt": _parse_xmltv_time(prog.get("start", "")),
            "stop_dt": _parse_xmltv_time(prog.get("stop", "")),
        }
        by_channel.setdefault(ch, []).append(entry)

    for programs in by_channel.values():
        programs.sort(key=lambda p: p["start_dt"])
    return by_channel


def now_next(programs: list) -> dict:
    now = datetime.now(timezone.utc)
    current = None
    upcoming = None
    for prog in programs:
        if prog["start_dt"] <= now < prog["stop_dt"]:
            current = prog
        elif prog["start_dt"] > now and upcoming is None:
            upcoming = prog
            break
    return {"now": current, "next": upcoming}


def match_channel_epg(channel: dict, epg_map: dict, xmltv_channels: dict) -> dict:
    """Match channel to EPG using tvg-id or display-name."""
    tvg = channel.get("tvg_id") or ""
    if tvg and tvg in epg_map:
        return now_next(epg_map[tvg])
    name = channel.get("name", "").lower()
    for xml_id, display in xmltv_channels.items():
        if display.lower() == name and xml_id in epg_map:
            return now_next(epg_map[xml_id])
    return {"now": None, "next": None}


def parse_channel_names(xml_text: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    names = {}
    for ch in root.findall("channel"):
        cid = ch.get("id", "")
        display = ch.find("display-name")
        if cid and display is not None and display.text:
            names[cid] = display.text.strip()
    return names

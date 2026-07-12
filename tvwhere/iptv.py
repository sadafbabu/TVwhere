import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from tvwhere.config import CACHE_DIR, CACHE_TTL, ensure_dirs

USER_AGENT = "TVwhere/2.1 (IPTV Player; +https://github.com/sadafbabu/TVwhere)"

_LOGO_RE = re.compile(r'tvg-logo="([^"]*)"', re.I)
_GROUP_RE = re.compile(r'group-title="([^"]*)"', re.I)
_TVG_NAME_RE = re.compile(r'tvg-name="([^"]*)"', re.I)
_TVG_ID_RE = re.compile(r'tvg-id="([^"]*)"', re.I)
from tvwhere.resolution import detect_resolution
_STREAM_PREFIXES = ("http://", "https://", "rtmp://", "rtsp://", "udp://")


def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def _cache_file(url: str):
    return CACHE_DIR / f"{get_url_hash(url)}.json"


def get_cached_playlist(url: str, allow_stale: bool = False) -> list:
    ensure_dirs()
    path = _cache_file(url)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if allow_stale or age < CACHE_TTL:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else None
        except Exception:
            return None
    return None


def save_to_cache(url: str, data: list):
    ensure_dirs()
    path = _cache_file(url)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"Cache write failed: {exc}")


def parse_m3u(content: str) -> list:
    content = content.replace("\r", "")
    lines = content.split("\n")

    channels = []
    seen_urls = set()
    current_meta = {}

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("#EXTINF:"):
            logo = _LOGO_RE.search(line)
            group = _GROUP_RE.search(line)
            tvg_name = _TVG_NAME_RE.search(line)
            tvg_id = _TVG_ID_RE.search(line)

            idx = line.rfind(",")
            comma_name = line[idx + 1 :].strip() if idx != -1 else "Unknown Channel"
            name = (tvg_name.group(1) if tvg_name else comma_name).strip() or comma_name

            grp = group.group(1) if group else "General"
            res_match = detect_resolution(name, grp)
            radio = grp.lower() in ("radio", "radios") or " radio" in name.lower()

            current_meta = {
                "name": name,
                "logo": logo.group(1) if logo else "",
                "group": grp,
                "resolution": res_match,
                "tvg_id": tvg_id.group(1) if tvg_id else "",
                "radio": radio,
            }
            continue

        if line.startswith("#"):
            continue

        if current_meta and line.lower().startswith(_STREAM_PREFIXES):
            url = line
            if url in seen_urls:
                current_meta = {}
                continue
            seen_urls.add(url)
            entry = dict(current_meta)
            entry["url"] = url
            channels.append(entry)
            current_meta = {}

    return channels


def parse_m3u_file(path: str) -> list:
    content = Path(path).read_text(encoding="utf-8", errors="ignore")
    return parse_m3u(content)


def load_m3u_from_path(path: str) -> list:
    """Load channels from a local .m3u / .m3u8 file."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"Playlist file not found: {path}")
    return parse_m3u_file(str(p))


def clear_playlist_cache(url: str):
    path = _cache_file(url)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def fetch_and_parse(url: str, callback, error_callback):
    cached = get_cached_playlist(url)
    if cached is not None:
        callback(cached, from_cache=True)
        return

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode("utf-8", errors="ignore")

        channels = parse_m3u(content)
        if channels:
            save_to_cache(url, channels)
            callback(channels, from_cache=False)
            return

        stale = get_cached_playlist(url, allow_stale=True)
        if stale:
            callback(stale, from_cache=True)
            return
        error_callback("Playlist is empty or could not be parsed.")
    except Exception as exc:
        stale = get_cached_playlist(url, allow_stale=True)
        if stale:
            callback(stale, from_cache=True)
            return
        if isinstance(exc, urllib.error.HTTPError):
            error_callback(f"HTTP {exc.code}: could not download playlist.")
        elif isinstance(exc, urllib.error.URLError):
            error_callback(f"Network error: {exc.reason}")
        else:
            error_callback(f"Failed to load playlist: {exc}")


def get_channels_async(url: str, callback, error_callback):
    thread = threading.Thread(
        target=fetch_and_parse,
        args=(url, callback, error_callback),
        daemon=True,
    )
    thread.start()

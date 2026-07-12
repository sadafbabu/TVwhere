"""Background channel health checks with cached results."""

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

from tvwhere.config import CACHE_DIR, ensure_dirs
from tvwhere.iptv import USER_AGENT
from tvwhere.models import channel_id

HEALTH_FILE = CACHE_DIR / "health.json"
HEALTH_TTL = 6 * 3600  # 6 hours
CHECK_TIMEOUT = 4
BATCH_SIZE = 4
BATCH_DELAY = 0.35

_lock = threading.Lock()
_cache = None
_checking = set()


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    ensure_dirs()
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE, encoding="utf-8") as f:
                _cache = json.load(f)
                return _cache if isinstance(_cache, dict) else {}
        except Exception:
            pass
    _cache = {}
    return _cache


def _save(data: dict):
    global _cache
    _cache = data
    ensure_dirs()
    try:
        with open(HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _key(url: str) -> str:
    return channel_id(url)


def get_status(url: str) -> Optional[bool]:
    """Return True=alive, False=dead, None=unknown/expired."""
    data = _load()
    entry = data.get(_key(url))
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > HEALTH_TTL:
        return None
    return entry.get("ok")


def set_status(url: str, ok: bool):
    with _lock:
        data = dict(_load())
        data[_key(url)] = {"ok": ok, "ts": time.time(), "url": url}
        _save(data)


def probe_url(url: str) -> bool:
    headers = {"User-Agent": USER_AGENT}
    try:
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
            return 200 <= resp.status < 400
    except Exception:
        pass
    try:
        req = urllib.request.Request(url, headers={**headers, "Range": "bytes=0-1"})
        with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as exc:
        return exc.code not in (404, 410, 403, 401)
    except Exception:
        return False


def filter_channels(channels: list, hide_dead: bool = True) -> list:
    if not hide_dead:
        return channels
    result = []
    for ch in channels:
        url = ch.get("url", "")
        status = get_status(url)
        if status is False:
            continue
        result.append(ch)
    return result


def check_channel(url: str) -> bool:
    if url in _checking:
        cached = get_status(url)
        return cached if cached is not None else True
    _checking.add(url)
    try:
        ok = probe_url(url)
        set_status(url, ok)
        return ok
    finally:
        _checking.discard(url)


def check_batch_async(
    channels: list,
    on_dead: Optional[Callable] = None,
    on_done: Optional[Callable] = None,
):
    """Check channels in background; hide only confirmed-dead."""

    def worker():
        pending = []
        for ch in channels:
            url = ch.get("url", "")
            if not url:
                continue
            status = get_status(url)
            if status is None:
                pending.append(url)

        any_dead = False
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i : i + BATCH_SIZE]
            for url in batch:
                was = get_status(url)
                ok = check_channel(url)
                if not ok and was is not False:
                    any_dead = True
                    if on_dead:
                        on_dead()
            time.sleep(BATCH_DELAY)

        if on_done:
            on_done(any_dead)

    threading.Thread(target=worker, daemon=True).start()

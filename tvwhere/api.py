"""HTTP API + web UI server for mobile and browser access."""

import json
import mimetypes
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tvwhere.config import FavoritesManager, ensure_dirs
from tvwhere.history import HistoryManager
from tvwhere.iptv import USER_AGENT
from tvwhere.models import channel_id
from tvwhere.playlists import PlaylistManager
from tvwhere.service import PlaylistService

WEB_ROOT = Path(__file__).resolve().parent / "web" / "static"
_CHANNEL_CACHE = {}
_STREAM_PREFIXES = ("http://", "https://")


def _json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if not length:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _safe_stream_url(url: str) -> bool:
    return url.lower().startswith(_STREAM_PREFIXES)


def _absolutize_url(base: str, ref: str) -> str:
    ref = ref.strip()
    if not ref or ref.startswith("#"):
        return ref
    if ref.startswith(("http://", "https://")):
        return ref
    return urllib.parse.urljoin(base, ref)


def _rewrite_m3u8(content: str, base_url: str, proxy_base: str) -> str:
    lines = []
    for line in content.replace("\r", "").split("\n"):
        if not line or line.startswith("#"):
            lines.append(line)
            continue
        abs_url = _absolutize_url(base_url, line)
        if _safe_stream_url(abs_url):
            enc = urllib.parse.quote(abs_url, safe="")
            lines.append(f"{proxy_base}{enc}")
        else:
            lines.append(line)
    return "\n".join(lines)


class TVwhereAPIHandler(BaseHTTPRequestHandler):
    server_version = "TVwhere/2.0"

    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/playlists":
            items = PlaylistService.list_playlists()
            safe = []
            for pl in items:
                entry = dict(pl)
                if entry.get("type") == "xtream":
                    entry["password"] = "••••"
                safe.append(entry)
            return _json_response(self, {"playlists": safe})

        if path.startswith("/api/playlists/") and path.endswith("/groups"):
            pid = path.split("/")[3]
            channels = _CHANNEL_CACHE.get(pid) or PlaylistService.load_channels_sync(pid)
            _CHANNEL_CACHE[pid] = channels
            return _json_response(self, {"groups": PlaylistService.get_groups(channels)})

        if path.startswith("/api/playlists/") and "/channels" in path:
            pid = path.split("/")[3]
            group = (query.get("group") or [""])[0]
            q = (query.get("q") or [""])[0]
            force = (query.get("refresh") or ["0"])[0] == "1"
            try:
                if force or pid not in _CHANNEL_CACHE:
                    _CHANNEL_CACHE[pid] = PlaylistService.load_channels_sync(pid, force=force)
                channels = _CHANNEL_CACHE[pid]
                result = PlaylistService.search(channels, q, group or None)
                return _json_response(self, {"channels": result, "total": len(result)})
            except Exception as exc:
                return _json_response(self, {"error": str(exc)}, 400)

        if path == "/api/favorites":
            favs = FavoritesManager.get_all()
            for f in favs:
                f.setdefault("id", channel_id(f.get("url", "")))
            return _json_response(self, {"channels": favs})

        if path == "/api/recent":
            return _json_response(self, {"channels": HistoryManager.get_all()})

        if path == "/api/epg":
            pid = (query.get("playlist") or [""])[0]
            cid = (query.get("channel") or [""])[0]
            try:
                pl = PlaylistManager.get(pid)
                if not pl:
                    return _json_response(self, {"now": None, "next": None})
                if pid not in _CHANNEL_CACHE:
                    _CHANNEL_CACHE[pid] = PlaylistService.load_channels_sync(pid)
                ch = next((c for c in _CHANNEL_CACHE[pid] if c.get("id") == cid), None)
                if not ch:
                    return _json_response(self, {"now": None, "next": None})
                epg = PlaylistService.get_epg_for_channel(ch, pl)
                for key in ("now", "next"):
                    if epg.get(key):
                        epg[key] = {
                            "title": epg[key].get("title", ""),
                            "description": epg[key].get("description", ""),
                            "start": epg[key].get("start", ""),
                            "stop": epg[key].get("stop", ""),
                        }
                return _json_response(self, epg)
            except Exception as exc:
                return _json_response(self, {"error": str(exc)}, 400)

        if path == "/api/stream":
            url = (query.get("url") or [""])[0]
            url = urllib.parse.unquote(url)
            if not _safe_stream_url(url):
                return _json_response(self, {"error": "Invalid stream URL"}, 400)
            return self._proxy_stream(url)

        if path == "/api/logo":
            url = (query.get("url") or [""])[0]
            url = urllib.parse.unquote(url)
            if not _safe_stream_url(url):
                self.send_error(400)
                return
            return self._proxy_binary(url)

        if path in ("/", "/index.html"):
            return self._serve_file(WEB_ROOT / "index.html")

        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            target = WEB_ROOT / rel
            if target.is_file():
                return self._serve_file(target)

        if path == "/manifest.json":
            return self._serve_file(WEB_ROOT / "manifest.json")

        if path == "/sw.js":
            return self._serve_file(WEB_ROOT / "sw.js")

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        data = _read_json(self)

        if path == "/api/playlists":
            ptype = data.get("type", "m3u")
            try:
                if ptype == "m3u":
                    url = data.get("url", "").strip()
                    if not url.startswith(("http://", "https://")):
                        return _json_response(self, {"error": "Invalid M3U URL"}, 400)
                    pl = PlaylistManager.add_m3u(
                        data.get("name", "M3U"), url, data.get("epg_url", "")
                    )
                elif ptype == "xtream":
                    from tvwhere.xtream import validate_login

                    server = data.get("server", "")
                    user = data.get("username", "")
                    password = data.get("password", "")
                    validate_login(server, user, password)
                    pl = PlaylistManager.add_xtream(
                        data.get("name", "Xtream"), server, user, password
                    )
                else:
                    return _json_response(self, {"error": "Unknown playlist type"}, 400)
                _CHANNEL_CACHE.pop(pl["id"], None)
                return _json_response(self, {"playlist": pl}, 201)
            except Exception as exc:
                return _json_response(self, {"error": str(exc)}, 400)

        if path == "/api/favorites":
            ch = data.get("channel")
            if not ch or not ch.get("url"):
                return _json_response(self, {"error": "Channel required"}, 400)
            FavoritesManager.add(
                ch.get("name", "Channel"),
                ch["url"],
                ch.get("group", "General"),
                ch.get("logo", ""),
            )
            return _json_response(self, {"ok": True})

        if path == "/api/play":
            ch = data.get("channel")
            if ch:
                PlaylistService.record_play(ch)
            return _json_response(self, {"ok": True})

        self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/playlists/"):
            pid = path.split("/")[-1]
            if PlaylistManager.remove(pid):
                _CHANNEL_CACHE.pop(pid, None)
                return _json_response(self, {"ok": True})
            return _json_response(self, {"error": "Cannot remove playlist"}, 400)

        if path.startswith("/api/favorites/"):
            name = urllib.parse.unquote(path.split("/")[-1])
            FavoritesManager.remove(name)
            return _json_response(self, {"ok": True})

        self.send_error(404)

    def _serve_file(self, path: Path):
        if not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        if path.suffix in (".html", ".js", ".css"):
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _proxy_binary(self, url: str):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "image/png")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_error(502)

    def _proxy_stream(self, url: str):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
            text = raw.decode("utf-8", errors="ignore")
            is_manifest = (
                url.endswith(".m3u8")
                or "mpegurl" in ctype.lower()
                or text.lstrip().startswith("#EXTM3U")
            )
            if is_manifest and "#EXT" in text:
                host = self.headers.get("Host", "localhost")
                scheme = "http"
                proxy_base = f"{scheme}://{host}/api/stream?url="
                body = _rewrite_m3u8(text, url, proxy_base).encode("utf-8")
                ctype = "application/vnd.apple.mpegurl"
            else:
                body = raw
            self.send_response(200)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.HTTPError as exc:
            self.send_error(exc.code)
        except Exception:
            self.send_error(502)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_server(host: str = "0.0.0.0", port: int = 8765):
    ensure_dirs()
    if not WEB_ROOT.is_dir():
        raise FileNotFoundError(f"Web UI not found: {WEB_ROOT}")

    httpd = ThreadingHTTPServer((host, port), TVwhereAPIHandler)
    lan = get_local_ip()
    print(f"TVwhere Web UI running:")
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  Network: http://{lan}:{port}  (phone/tablet on same Wi-Fi)")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()

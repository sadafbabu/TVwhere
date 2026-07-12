# TVwhere

Cross-platform IPTV player for **Windows, Linux, macOS, and mobile** (phone/tablet browser).

Inspired by open projects like [IPTVnator](https://github.com/4gray/iptvnator), [Fred TV](https://github.com/Fredolx/open-tv), and [OpenTV Player](https://github.com/jaccon/opentv-player) — built as pure Python with zero pip dependencies.

- **Desktop app** — Tkinter UI, opens streams in **mpv** or **VLC**
- **Web / PWA** — responsive UI with built-in HLS player; works on any phone on the same Wi-Fi

## Features

### Desktop
- Black & gray minimalist UI
- Bangladesh / Bengali / Global playlists ([iptv-org](https://github.com/iptv-org/iptv))
- **Group filter** — browse by category
- **Recent channels** — watch history
- Fast search — multi-word, accent-insensitive, relevance-ranked
- Favorites, custom M3U URL
- Playlist cache with offline stale fallback
- Keyboard shortcuts: Ctrl+F search, Ctrl+R refresh, Esc clear
- Remembers last tab between sessions

### Web / Mobile (`tvwhere --web`)
- Responsive UI — phone, tablet, desktop browser
- **Install as PWA** on Android/iOS (Add to Home Screen)
- Built-in **HLS player** (HLS.js) with stream proxy
- **Channel logos** in list
- **Group filter** dropdown
- Add **M3U URL** or **Xtream Codes** playlists
- Favorites & recent channels
- Access from phone: `http://<your-pc-ip>:8765`

## Requirements

| Platform | Python | Player |
|----------|--------|--------|
| Desktop  | 3.8+ with tkinter | mpv or VLC (recommended) |
| Web/Mobile | 3.8+ only | Built-in browser player |

### Install player (desktop external playback)

**Windows**
```powershell
winget install mpv
```

**Linux (Arch)**
```bash
sudo pacman -S python tk mpv
```

**macOS**
```bash
brew install python-tk mpv
```

## Quick start

```bash
git clone https://github.com/sadafbabu/TVwhere.git
cd TVwhere
python3 -m tvwhere          # desktop app
python3 -m tvwhere --web --open   # web UI + open browser
```

On Windows: `py -m tvwhere` or `py -m tvwhere --web --open`

## Web / mobile mode

Start the server on your PC:

```bash
python3 -m tvwhere --web --port 8765
```

Then on your phone (same Wi-Fi):

1. Open `http://<PC-IP>:8765` (IP shown in terminal)
2. Tap **Add playlist** (+) for M3U or Xtream Codes
3. Tap a channel to play in-browser
4. **Install PWA**: browser menu → Add to Home Screen

### Xtream Codes

In the web UI or API, add a playlist with:
- Server URL (e.g. `http://provider:8080`)
- Username & password

TVwhere fetches live channels via the Xtream API (same method used by OTT Navigator / IPTVnator).

## Desktop shortcuts

| Key | Action |
|-----|--------|
| Ctrl+F | Focus search |
| Ctrl+R | Refresh playlist |
| Esc | Clear search |

Sidebar **Web UI (mobile)** starts the server and opens the browser.

## Install launcher

**Linux / macOS**
```bash
./scripts/install.sh
tvwhere              # desktop
tvwhere-web          # web server
```

**Windows**
```powershell
.\scripts\install.ps1
tvwhere
tvwhere-web
```

## Data locations

| Data | Windows | Linux / macOS |
|------|---------|---------------|
| Config / favorites | `%APPDATA%\tvwhere\` | `~/.config/tvwhere/` |
| Cache | `%LOCALAPPDATA%\tvwhere\cache\` | `~/.cache/tvwhere/` |

## Project layout

```
TVwhere/
├── assets/              Icons (PNG, SVG, ICO)
├── scripts/             install.sh, install.ps1
├── tvwhere/
│   ├── app.py           Desktop Tkinter app
│   ├── api.py           Web server + REST API
│   ├── web/static/      PWA frontend (HTML/JS/CSS)
│   ├── xtream.py        Xtream Codes API
│   ├── iptv.py          M3U parser + cache
│   ├── service.py       Shared business logic
│   ├── epg.py           XMLTV EPG parser
│   ├── playlists.py     Multi-playlist manager
│   ├── history.py       Recent channels
│   └── player.py        mpv / VLC launcher
└── README.md
```

## API (for custom clients)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/playlists` | GET | List playlists |
| `/api/playlists` | POST | Add M3U or Xtream |
| `/api/playlists/{id}/channels` | GET | Channels (`?group=&q=`) |
| `/api/playlists/{id}/groups` | GET | Category list |
| `/api/favorites` | GET/POST | Favorites |
| `/api/recent` | GET | Watch history |
| `/api/epg?playlist=&channel=` | GET | EPG now/next (if epg_url set) |
| `/api/stream?url=` | GET | HLS stream proxy |

## Uninstall

```bash
./scripts/uninstall.sh    # Linux/macOS
.\scripts\uninstall.ps1   # Windows
```

## Inspired by open-source IPTV players

TVwhere takes design ideas from these MIT/GPL projects (no proprietary code copied):

| Project | What we adopted |
|---------|-----------------|
| [IPTVnator](https://github.com/4gray/iptvnator) | M3U + Xtream, EPG/XMLTV, group lists, favorites, PWA |
| [Fred TV / open-tv](https://github.com/Fredolx/open-tv) | Multi-source playlists, fast search, refresh |
| [OpenTV Player](https://github.com/jaccon/opentv-player) | Web server mode, HLS.js + stream proxy for mobile |
| [Extreme-InfiniTV](https://github.com/infinitel8p/Extreme-InfiniTV) | Xtream login, category groups, cross-platform |
| [iptv-org](https://github.com/iptv-org/iptv) | Free Bangladesh / Global M3U sources |

## License

MIT — see [LICENSE](LICENSE).

Inspired by open-source IPTV projects; no proprietary code copied.

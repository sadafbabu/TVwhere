# TVwhere

Minimalist IPTV player for **Windows, Linux, and macOS**.

Pure Python + Tkinter. No pip dependencies. Streams open in **mpv** (recommended) or **VLC**.

## Features

- Black & gray UI — clean, readable, nothing flashy
- Bangladesh / Bengali / Global playlists from [iptv-org](https://github.com/iptv-org/iptv)
- Fast search — multi-word, accent-insensitive, debounced
- Favorites saved locally
- Lazy channel list (smooth with 10,000+ channels)
- Custom M3U URL support
- Playlist cache (1 hour) under your OS app-data folder

## Requirements

| Platform | Python | Player |
|----------|--------|--------|
| Windows  | 3.8+ with tkinter | mpv or VLC |
| Linux    | 3.8+ with tkinter | mpv or VLC |
| macOS    | 3.8+ with tkinter | mpv or VLC |

### Install player

**Windows**
```powershell
winget install mpv
# or download VLC from https://www.videolan.org/
```

**Linux (Arch)**
```bash
sudo pacman -S python tk mpv
```

**macOS**
```bash
brew install python-tk mpv
```

## Run

### Quick start (any OS)

```bash
git clone https://github.com/sadafbabu/TVwhere.git
cd TVwhere
python -m tvwhere
```

On Windows use `py -m tvwhere` if `python` is not on PATH.

### Linux / macOS — app menu shortcut

```bash
./scripts/install.sh
tvwhere
```

### Windows — desktop shortcut

```powershell
.\scripts\install.ps1
tvwhere
```

## Data locations

| Data | Windows | Linux / macOS |
|------|---------|---------------|
| Favorites | `%APPDATA%\tvwhere\` | `~/.config/tvwhere/` |
| Cache | `%LOCALAPPDATA%\tvwhere\cache\` | `~/.cache/tvwhere/` |

## Branding

App icon and logo live in `assets/`:

- `icon.svg` — source vector (black/gray TV + play)
- `icon.png` / `icon-*.png` — PNG sizes for Linux desktop
- `icon.ico` — Windows taskbar / shortcut

Regenerate all sizes:

```bash
python3 scripts/generate_icons.py
```

## Project layout

```
TVwhere/
├── assets/icon.png      App icon
├── scripts/
│   ├── install.sh       Linux / macOS launcher
│   ├── install.ps1      Windows launcher
│   └── uninstall.sh
├── tvwhere/             Python package
│   ├── app.py           Main window
│   ├── config.py        Theme, paths, playlists
│   ├── search.py        Search engine
│   ├── iptv.py          M3U fetch + cache
│   ├── player.py        mpv / VLC launcher
│   └── widgets.py       UI components
├── setup.py
└── README.md
```

## Uninstall launcher

**Linux / macOS**
```bash
./scripts/uninstall.sh
```

**Windows**
```powershell
.\scripts\uninstall.ps1
```

## License

MIT — see [LICENSE](LICENSE).

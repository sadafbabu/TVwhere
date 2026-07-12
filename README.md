# TVwhere

A highly polished, minimalist, dark-themed IPTV Player written in pure Python + Tkinter. No external Python packages are required (runs entirely on standard libraries).

## Features
- **Minimalist Dark Theme** using custom tkinter components.
- **Auto-Fetching Playlists:** Loads curated live TV lists (Bangladesh, Bengali, Global 13k+ channels) from `iptv-org`.
- **Fast Search:** Filter channels in real-time.
- **Favorites:** Toggle favorite state (`★`) and browse in the dedicated Favorites tab.
- **Auto-Player Detection:** Spawns stream instantly in `mpv` (recommended for zero-latency buffering and full player control) or falls back to `vlc`.
- **Custom Playlists:** Input any custom M3U playlist URL.
- **Offline Caching:** Playlists are parsed and cached locally under `~/.cache/tvwhere/` (1 hour TTL) to load instantly.

## Requirements
- Python 3.8+ (with `tkinter`)
- `mpv` (recommended) or `vlc` player

On Arch Linux:
```bash
sudo pacman -S python mpv
```

## Running the App
From the project root directory, run:
```bash
python3 -m tvwhere
```

## Desktop Integration (Linux)
A desktop launcher file is included. To make TVwhere available in your application menus (like `rofi`, `wofi`, `dmenu`):
```bash
# 1. Install pip package in editable mode
pip install -e .

# 2. Copy the desktop entry to your user applications
cp tvwhere.desktop ~/.local/share/applications/
```

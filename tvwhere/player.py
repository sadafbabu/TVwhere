import os
import platform
import shutil
import subprocess


class PlayerManager:
    """Spawn mpv or VLC for stream playback (Windows / Linux / macOS)."""

    def __init__(self):
        self._process = None
        self._player = self._detect_player()
        self._player_cmd = self._resolve_command(self._player) if self._player else None

    def _detect_player(self):
        if shutil.which("mpv"):
            return "mpv"
        if shutil.which("vlc"):
            return "vlc"

        system = platform.system()

        if system == "Darwin":
            vlc_app = "/Applications/VLC.app/Contents/MacOS/VLC"
            if os.path.isfile(vlc_app):
                return "vlc"
            if os.path.isfile("/opt/homebrew/bin/mpv"):
                return "mpv"

        if system == "Linux":
            flatpak_mpv = "/var/lib/flatpak/exports/bin/io.mpv.Mpv"
            if os.path.isfile(flatpak_mpv):
                return "mpv"

        if os.name == "nt":
            local = os.environ.get("LOCALAPPDATA", "")
            candidates = [
                os.path.join(local, "Programs", "mpv", "mpv.exe"),
                os.path.join(local, "Programs", "MPV", "mpv.exe"),
                r"C:\Program Files\mpv\mpv.exe",
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            ]
            for path in candidates:
                if os.path.isfile(path):
                    return "mpv" if path.lower().endswith("mpv.exe") else "vlc"

        return None

    def _resolve_command(self, player: str):
        if player == "mpv":
            if shutil.which("mpv"):
                return ["mpv"]
            if platform.system() == "Darwin" and os.path.isfile("/opt/homebrew/bin/mpv"):
                return ["/opt/homebrew/bin/mpv"]
            if platform.system() == "Linux":
                flatpak = "/var/lib/flatpak/exports/bin/io.mpv.Mpv"
                if os.path.isfile(flatpak):
                    return [flatpak]
            if os.name == "nt":
                local = os.environ.get("LOCALAPPDATA", "")
                for path in (
                    os.path.join(local, "Programs", "mpv", "mpv.exe"),
                    os.path.join(local, "Programs", "MPV", "mpv.exe"),
                    r"C:\Program Files\mpv\mpv.exe",
                ):
                    if os.path.isfile(path):
                        return [path]
        elif player == "vlc":
            if shutil.which("vlc"):
                return ["vlc"]
            if platform.system() == "Darwin":
                app = "/Applications/VLC.app/Contents/MacOS/VLC"
                if os.path.isfile(app):
                    return [app]
            if os.name == "nt":
                for path in (
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                ):
                    if os.path.isfile(path):
                        return [path]
        return None

    @property
    def player_name(self) -> str:
        return self._player if self._player else "None"

    def play(self, url: str, title: str = "") -> bool:
        self.stop()
        if not self._player_cmd:
            return False

        label = title or "TVwhere"
        if self._player == "mpv":
            args = self._player_cmd + [
                "--no-terminal",
                "--really-quiet",
                "--force-window=immediate",
                "--cache=yes",
                f"--title={label}",
                url,
            ]
        else:
            args = self._player_cmd + [
                "--no-video-title-show",
                "--intf",
                "dummy",
                "--meta-title",
                label,
                url,
            ]

        try:
            kwargs = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if os.name == "nt":
                kwargs["creationflags"] = 0x08000000
            self._process = subprocess.Popen(args, **kwargs)
            return True
        except Exception as exc:
            print(f"Player launch failed: {exc}")
            return False

    def stop(self):
        if not self._process:
            return
        try:
            self._process.terminate()
            self._process.wait(timeout=2)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass
        self._process = None

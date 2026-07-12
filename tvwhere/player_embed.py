"""In-app video playback — mpv embedded in Tk frame, web player fallback."""

import os
import shutil
import subprocess


class EmbeddedPlayer:
    """Play streams inside the app window when possible."""

    def __init__(self, parent_frame, web_port: int = 8765):
        self.frame = parent_frame
        self.web_port = web_port
        self._process = None
        self._mpv_cmd = self._find_mpv()

    def _find_mpv(self):
        if shutil.which("mpv"):
            return ["mpv"]
        flatpak = "/var/lib/flatpak/exports/bin/io.mpv.Mpv"
        if os.path.isfile(flatpak):
            return [flatpak]
        return None

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

    def _try_mpv_embed(self, url: str, title: str) -> bool:
        if not self._mpv_cmd:
            return False
        self.stop()
        self.frame.update_idletasks()
        wid = self.frame.winfo_id()
        if not wid:
            return False
        args = self._mpv_cmd + [
            f"--wid={int(wid)}",
            "--no-terminal",
            "--really-quiet",
            "--keep-open=yes",
            "--osd-bar=no",
            "--cache=yes",
            f"--title={title}",
            url,
        ]
        try:
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if os.name == "nt":
                kwargs["creationflags"] = 0x08000000
            self._process = subprocess.Popen(args, **kwargs)
            return self._process.poll() is None
        except Exception:
            return False

    def _try_mpv_geometry(self, url: str, title: str) -> bool:
        if not self._mpv_cmd:
            return False
        self.stop()
        self.frame.update_idletasks()
        w = max(self.frame.winfo_width(), 400)
        h = max(self.frame.winfo_height(), 200)
        x = self.frame.winfo_rootx()
        y = self.frame.winfo_rooty()
        geom = f"{w}x{h}+{x}+{y}"
        args = self._mpv_cmd + [
            f"--geometry={geom}",
            "--no-border",
            "--ontop",
            "--no-terminal",
            "--really-quiet",
            "--keep-open=yes",
            "--cache=yes",
            f"--title={title}",
            url,
        ]
        try:
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if os.name == "nt":
                kwargs["creationflags"] = 0x08000000
            self._process = subprocess.Popen(args, **kwargs)
            return self._process.poll() is None
        except Exception:
            return False

    def play(self, url: str, title: str = "", on_web=None) -> str:
        label = title or "TVwhere"
        if self._try_mpv_embed(url, label):
            return "embed"
        if self._try_mpv_geometry(url, label):
            return "embed"
        if on_web:
            on_web(url, label)
            return "web"
        return "none"

import subprocess
import shutil
import os
import platform

class PlayerManager:
    """Manages spawning and killing media player processes (mpv / vlc)."""
    def __init__(self):
        self._process = None
        self._detected_player = self._detect_player()

    def _detect_player(self) -> str:
        """Detect if mpv or vlc is installed."""
        if shutil.which("mpv"):
            return "mpv"
        if shutil.which("vlc"):
            return "vlc"
        
        # macOS specific fallback for VLC
        if platform.system() == "Darwin":
            if os.path.exists("/Applications/VLC.app/Contents/MacOS/VLC"):
                return "vlc"
                
        return None

    @property
    def player_name(self) -> str:
        """Return the name of the detected player, or None."""
        return self._detected_player if self._detected_player else "None"

    def is_playing(self) -> bool:
        """Check if a stream is currently active."""
        if self._process:
            return self._process.poll() is None
        return False

    def play(self, url: str, title: str = "") -> bool:
        """Launch the media player with the stream URL. Non-blocking."""
        self.stop()  # Stop any existing stream first

        if not self._detected_player:
            return False

        args = []
        if self._detected_player == "mpv":
            args = [
                "mpv",
                "--force-window=immediate",
                "--cache=yes",
                f"--title={title if title else 'TVwhere'}",
                url
            ]
        elif self._detected_player == "vlc":
            if platform.system() == "Darwin" and not shutil.which("vlc"):
                # macOS direct app bundle execution
                args = [
                    "/Applications/VLC.app/Contents/MacOS/VLC",
                    "--meta-title", title if title else "TVwhere",
                    url
                ]
            else:
                args = [
                    "vlc",
                    "--meta-title", title if title else "TVwhere",
                    url
                ]

        try:
            # Set creationflags on Windows to avoid opening a command prompt window
            creationflags = 0
            if os.name == 'nt':
                # CREATE_NO_WINDOW
                creationflags = 0x08000000

            self._process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            return True
        except Exception as e:
            print(f"Error launching player: {e}")
            return False

    def stop(self):
        """Terminate the running stream process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

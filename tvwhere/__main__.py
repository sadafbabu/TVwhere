import argparse
import os
import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser

from tvwhere import __version__
from tvwhere.app import TVwhereApp
from tvwhere.icons import apply_window_icon


def _has_gui() -> bool:
    if sys.platform == "win32" or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _open_browser(url: str):
    if sys.platform.startswith("linux"):
        for cmd, args in (
            ("xdg-open", [url]),
            ("gio", ["open", url]),
            ("wslview", [url]),
        ):
            if shutil.which(cmd):
                try:
                    subprocess.Popen(
                        [cmd, *args] if cmd != "xdg-open" else [cmd, url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except OSError:
                    pass
    webbrowser.open(url)


def _center_window(root: tk.Tk, width: int = 980, height: int = 700):
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")


def run_desktop():
    if not _has_gui():
        print("No display found. Use: tvwhere --web --open", file=sys.stderr)
        sys.exit(1)

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Could not open TVwhere window: {exc}", file=sys.stderr)
        print("Try: tvwhere --web --open", file=sys.stderr)
        sys.exit(1)

    try:
        if sys.platform == "win32":
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
            root.tk.call("tk", "scaling", 1.25)
        elif sys.platform.startswith("linux"):
            root.wm_class("tvwhere", "TVwhere")
    except Exception:
        pass

    root.title(f"TVwhere {__version__}")
    root._tvwhere_icon = apply_window_icon(root)
    _center_window(root)

    app = TVwhereApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


def run_web(host: str, port: int, open_browser: bool):
    from tvwhere.api import run_server

    if open_browser:
        import threading

        def _open():
            import time

            time.sleep(0.8)
            _open_browser(f"http://127.0.0.1:{port}")

        threading.Thread(target=_open, daemon=True).start()

    run_server(host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="TVwhere — cross-platform IPTV player")
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Open desktop window with channel list (default when GUI available)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web UI server only (mobile, tablet, browser)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web server bind address")
    parser.add_argument("--port", type=int, default=8765, help="Web server port")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open browser when starting web server",
    )
    args = parser.parse_args()

    if args.web:
        run_web(args.host, args.port, args.open or not args.desktop)
    elif args.desktop:
        run_desktop()
    else:
        # Default: show desktop window — what users expect from app menu / tvwhere
        if _has_gui():
            run_desktop()
        else:
            run_web(args.host, args.port, True)


def main_web():
    """Entry point for tvwhere-web console script."""
    run_web("0.0.0.0", 8765, True)


if __name__ == "__main__":
    main()

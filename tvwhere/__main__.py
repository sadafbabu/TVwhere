import argparse
import sys
import tkinter as tk
import webbrowser

from tvwhere import __version__
from tvwhere.app import TVwhereApp
from tvwhere.icons import apply_window_icon


def _center_window(root: tk.Tk, width: int = 980, height: int = 700):
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")


def run_desktop():
    root = tk.Tk()

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

            time.sleep(0.6)
            webbrowser.open(f"http://127.0.0.1:{port}")

        threading.Thread(target=_open, daemon=True).start()

    run_server(host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="TVwhere — cross-platform IPTV player")
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Classic desktop UI with channel list (default is web player)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web UI server (mobile, tablet, browser)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web server bind address")
    parser.add_argument("--port", type=int, default=8765, help="Web server port")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open browser when starting web server",
    )
    args = parser.parse_args()

    if args.desktop:
        run_desktop()
    elif args.web:
        run_web(args.host, args.port, args.open)
    else:
        run_web(args.host, args.port, True)


if __name__ == "__main__":
    main()

import sys
import tkinter as tk

from tvwhere.app import TVwhereApp
from tvwhere.icons import apply_window_icon


def main():
    root = tk.Tk()

    try:
        if sys.platform == "win32":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
            root.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass

    root._tvwhere_icon = apply_window_icon(root)

    app = TVwhereApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

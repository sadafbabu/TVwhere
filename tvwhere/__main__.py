import sys
import tkinter as tk

from tvwhere.app import TVwhereApp
from tvwhere.config import ICON_PATH


def main():
    root = tk.Tk()

    try:
        if sys.platform == "win32":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
            root.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass

    if ICON_PATH:
        try:
            root._tvwhere_icon = tk.PhotoImage(file=str(ICON_PATH))
            root.iconphoto(True, root._tvwhere_icon)
        except Exception:
            pass

    app = TVwhereApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

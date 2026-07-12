import tkinter as tk
import sys
from tvwhere.app import TVwhereApp

def main():
    root = tk.Tk()
    
    # Custom premium window icon if available
    try:
        # Cross-platform window scaling (HiDPI support)
        if sys.platform == "win32":
            root.tk.call('tk', 'scaling', 1.5)
    except Exception:
        pass
        
    app = TVwhereApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()

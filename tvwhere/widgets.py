import tkinter as tk
from tvwhere.config import THEME, FONTS


def set_bg_recursive(widget, color):
    try:
        if not getattr(widget, "_skip_hover_bg", False):
            widget.configure(bg=color)
    except Exception:
        pass
    for child in widget.winfo_children():
        set_bg_recursive(child, color)


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, on_near_bottom=None, *args, **kwargs):
        kwargs["bg"] = kwargs.get("bg", THEME["bg"])
        super().__init__(parent, *args, **kwargs)

        self.on_near_bottom = on_near_bottom
        self._near_bottom_armed = True

        self.canvas = tk.Canvas(
            self,
            bg=THEME["bg"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            bg=THEME["bg"],
            troughcolor=THEME["scrollbar"],
            activebackground=THEME["scrollbar_active"],
            bd=0,
            width=8,
        )

        self.inner_frame = tk.Frame(self.canvas, bg=THEME["bg"])
        self.inner_frame_id = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw"
        )

        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(self)

    def _on_scroll(self, first, last):
        self.scrollbar.set(first, last)
        try:
            near_bottom = float(last) >= 0.92
        except (TypeError, ValueError):
            return
        if near_bottom and self._near_bottom_armed and self.on_near_bottom:
            self._near_bottom_armed = False
            self.on_near_bottom()
            self.after(150, self._rearm_near_bottom)
        elif not near_bottom:
            self._near_bottom_armed = True

    def _rearm_near_bottom(self):
        self._near_bottom_armed = True

    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def bind_mousewheel(self, widget):
        widget.bind("<Enter>", self._bind_all)
        widget.bind("<Leave>", self._unbind_all)
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _bind_all(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_all(self, _event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")
        elif event.delta:
            delta = int(-1 * (event.delta / 120))
            if delta == 0:
                delta = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(delta * 3, "units")

    def clear(self):
        for child in self.inner_frame.winfo_children():
            child.destroy()
        self._near_bottom_armed = True
        self.canvas.yview_moveto(0)


class SearchEntry(tk.Frame):
    def __init__(self, parent, placeholder="Search channels...", on_change=None, on_escape=None, *args, **kwargs):
        super().__init__(parent, bg=THEME["border"], bd=1, *args, **kwargs)
        self.placeholder = placeholder
        self.on_change = on_change
        self.on_escape = on_escape

        inner = tk.Frame(self, bg=THEME["search_bg"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_write)

        self.entry = tk.Entry(
            inner,
            textvariable=self.var,
            bg=THEME["search_bg"],
            fg=THEME["fg"],
            insertbackground=THEME["fg"],
            font=FONTS["search"],
            bd=0,
            relief="flat",
            highlightthickness=0,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(10, 4), pady=7)

        self.clear_btn = tk.Label(
            inner,
            text="x",
            bg=THEME["search_bg"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            cursor="hand2",
            padx=8,
        )
        self.clear_btn._skip_hover_bg = True
        self.clear_btn.pack(side="right")
        self.clear_btn.bind("<Button-1>", self._clear_click)
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.configure(fg=THEME["fg"]))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.configure(fg=THEME["fg_dim"]))

        self.placeholder_active = True
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=THEME["fg_dim"])
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Escape>", self._on_escape_key)

    def _on_escape_key(self, _event):
        if self.on_escape:
            return self.on_escape()
        return None

    def _on_write(self, *_args):
        if not self.placeholder_active and self.on_change:
            self.on_change(self.var.get())

    def _on_focus_in(self, _event):
        if self.placeholder_active:
            self.placeholder_active = False
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=THEME["fg"])

    def _on_focus_out(self, _event):
        if not self.entry.get():
            self.placeholder_active = True
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=THEME["fg_dim"])

    def _clear_click(self, _event):
        self.clear()

    def get_text(self) -> str:
        if self.placeholder_active:
            return ""
        return self.var.get().strip()

    def clear(self):
        self.var.set("")
        self._on_focus_out(None)

    def focus(self):
        self.entry.focus_set()
        self._on_focus_in(None)


class ChannelCard(tk.Frame):
    def __init__(
        self,
        parent,
        name,
        group,
        resolution,
        is_fav,
        on_click,
        on_fav_toggle,
        on_hover=None,
        logo="",
        *args,
        **kwargs,
    ):
        super().__init__(parent, bg=THEME["bg_card"], cursor="hand2", *args, **kwargs)
        self.on_click = on_click
        self.on_fav_toggle = on_fav_toggle
        self.on_hover = on_hover
        self.is_fav = is_fav

        self.pack_propagate(False)
        self.configure(height=48)

        content = tk.Frame(self, bg=THEME["bg_card"])
        content.pack(fill="both", expand=True, padx=10, pady=5)

        initial = (name.strip()[:1] or "?").upper()
        avatar = tk.Label(
            content,
            text=initial,
            bg=THEME["badge_bg"],
            fg=THEME["fg_accent"],
            font=FONTS["small"],
            width=2,
        )
        avatar._skip_hover_bg = True
        avatar.pack(side="left", padx=(0, 6))

        star = "★" if is_fav else "☆"
        star_color = THEME["fg_accent"] if is_fav else THEME["fg_dim"]
        self.star_label = tk.Label(
            content,
            text=star,
            bg=THEME["bg_card"],
            fg=star_color,
            font=FONTS["body"],
            cursor="hand2",
            width=2,
        )
        self.star_label._skip_hover_bg = True
        self.star_label.pack(side="left")
        self.star_label.bind("<Button-1>", self._on_star_click)

        display_name = name if len(name) <= 64 else name[:61] + "..."
        self.name_label = tk.Label(
            content,
            text=display_name,
            bg=THEME["bg_card"],
            fg=THEME["fg"],
            font=FONTS["body"],
            anchor="w",
        )
        self.name_label.pack(side="left", fill="both", expand=True, padx=(4, 8))

        badges = tk.Frame(content, bg=THEME["bg_card"])
        badges.pack(side="right")

        if resolution:
            res = tk.Label(
                badges,
                text=resolution.upper(),
                bg=THEME["badge_bg"],
                fg=THEME["badge_fg"],
                font=FONTS["small"],
                padx=5,
                pady=1,
            )
            res._skip_hover_bg = True
            res.pack(side="right", padx=(4, 0))

        if group and group != "General":
            label = group[:14] + ".." if len(group) > 16 else group
            grp = tk.Label(
                badges,
                text=label,
                bg=THEME["badge_bg"],
                fg=THEME["fg_dim"],
                font=FONTS["small"],
                padx=5,
                pady=1,
            )
            grp._skip_hover_bg = True
            grp.pack(side="right")

        self._bind_hover(self)
        self._bind_hover(content)
        for child in content.winfo_children():
            if child is not self.star_label:
                self._bind_hover(child)

    def _bind_hover(self, widget):
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._on_card_click)

    def _on_star_click(self, event):
        self.is_fav = not self.is_fav
        self.star_label.configure(
            text="★" if self.is_fav else "☆",
            fg=THEME["fg_accent"] if self.is_fav else THEME["fg_dim"],
        )
        if self.on_fav_toggle:
            self.on_fav_toggle(self.is_fav)
        return "break"

    def _on_card_click(self, _event):
        if self.on_click:
            self.on_click()

    def _on_enter(self, _event):
        set_bg_recursive(self, THEME["bg_hover"])
        if self.on_hover:
            self.on_hover()

    def _on_leave(self, _event):
        set_bg_recursive(self, THEME["bg_card"])


class SidebarButton(tk.Frame):
    def __init__(self, parent, text, on_click, *args, **kwargs):
        super().__init__(parent, bg=THEME["bg_secondary"], cursor="hand2", *args, **kwargs)
        self.on_click = on_click
        self.is_active = False

        self.pack_propagate(False)
        self.configure(height=36)

        self.indicator = tk.Frame(self, bg=THEME["bg_secondary"], width=2)
        self.indicator.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=THEME["bg_secondary"])
        self.content.pack(side="left", fill="both", expand=True, padx=10)

        self.label = tk.Label(
            self.content,
            text=text,
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["heading"],
            anchor="w",
        )
        self.label.pack(fill="both", expand=True)

        for w in (self, self.content, self.label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.configure(bg=THEME["bg_active"])
            set_bg_recursive(self.content, THEME["bg_active"])
            self.indicator.configure(bg=THEME["fg_accent"])
            self.label.configure(fg=THEME["fg"])
        else:
            self.configure(bg=THEME["bg_secondary"])
            set_bg_recursive(self.content, THEME["bg_secondary"])
            self.indicator.configure(bg=THEME["bg_secondary"])
            self.label.configure(fg=THEME["fg_dim"])

    def _on_click(self, _event):
        if self.on_click:
            self.on_click()

    def _on_enter(self, _event):
        if not self.is_active:
            self.configure(bg=THEME["bg_hover"])
            set_bg_recursive(self.content, THEME["bg_hover"])

    def _on_leave(self, _event):
        if not self.is_active:
            self.configure(bg=THEME["bg_secondary"])
            set_bg_recursive(self.content, THEME["bg_secondary"])


class StatusBar(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg=THEME["bg_secondary"], bd=0, *args, **kwargs)

        self.left_label = tk.Label(
            self,
            text="Ready",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            padx=12,
            pady=5,
        )
        self.left_label.pack(side="left")

        self.right_label = tk.Label(
            self,
            text="0 channels",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            padx=12,
            pady=5,
        )
        self.right_label.pack(side="right")

    def set_status(self, text: str):
        self.left_label.configure(text=text)

    def set_count(self, count: int):
        self.right_label.configure(text=f"{count} channels")


class LoadingIndicator(tk.Label):
    def __init__(self, parent, *args, **kwargs):
        kwargs.setdefault("bg", THEME["bg"])
        kwargs.setdefault("fg", THEME["fg_dim"])
        kwargs.setdefault("font", FONTS["body"])
        super().__init__(parent, text="Loading channels", *args, **kwargs)
        self.dots = 0
        self.running = False
        self._message = "Loading channels"

    def set_message(self, message: str):
        self._message = message

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False

    def _animate(self):
        if not self.running:
            return
        self.dots = (self.dots + 1) % 4
        self.configure(text=f"{self._message}{'.' * self.dots}")
        self.after(400, self._animate)


class EmptyState(tk.Frame):
    def __init__(self, parent, title: str, subtitle: str, *args, **kwargs):
        super().__init__(parent, bg=THEME["bg"], *args, **kwargs)
        tk.Label(
            self,
            text=title,
            bg=THEME["bg"],
            fg=THEME["fg_dim"],
            font=FONTS["heading"],
        ).pack(pady=(40, 6))
        tk.Label(
            self,
            text=subtitle,
            bg=THEME["bg"],
            fg=THEME["empty_fg"],
            font=FONTS["small"],
            wraplength=420,
            justify="center",
        ).pack()


class UrlDialog(tk.Toplevel):
    """Themed dialog for custom M3U URLs (replaces system simpledialog)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Custom Playlist")
        self.configure(bg=THEME["bg_secondary"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self,
            text="Enter M3U playlist URL",
            bg=THEME["bg_secondary"],
            fg=THEME["fg"],
            font=FONTS["heading"],
            padx=20,
            pady=(16, 8),
        ).pack()

        entry_frame = tk.Frame(self, bg=THEME["border"], padx=20)
        entry_frame.pack(fill="x")

        inner = tk.Frame(entry_frame, bg=THEME["search_bg"])
        inner.pack(fill="x", padx=1, pady=1)

        self.entry = tk.Entry(
            inner,
            bg=THEME["search_bg"],
            fg=THEME["fg"],
            insertbackground=THEME["fg"],
            font=FONTS["body"],
            bd=0,
            relief="flat",
            highlightthickness=0,
            width=48,
        )
        self.entry.pack(fill="x", padx=8, pady=8)
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._ok())
        self.entry.bind("<Escape>", lambda e: self._cancel())
        self.entry.bind("<Key>", self._on_key)

        self.error_label = tk.Label(
            self,
            text="",
            bg=THEME["bg_secondary"],
            fg=THEME["error_fg"],
            font=FONTS["small"],
            padx=20,
        )
        self.error_label.pack(anchor="w")

        btn_row = tk.Frame(self, bg=THEME["bg_secondary"], pady=14, padx=20)
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
            text="Paste",
            command=self._paste,
            bg=THEME["bg_card"],
            fg=THEME["fg_dim"],
            activebackground=THEME["bg_hover"],
            activeforeground=THEME["fg"],
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="left")

        tk.Button(
            btn_row,
            text="Cancel",
            command=self._cancel,
            bg=THEME["bg_card"],
            fg=THEME["fg_dim"],
            activebackground=THEME["bg_hover"],
            activeforeground=THEME["fg"],
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            btn_row,
            text="Load",
            command=self._ok,
            bg=THEME["bg_active"],
            fg=THEME["fg"],
            activebackground=THEME["bg_hover"],
            activeforeground=THEME["fg"],
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _on_key(self, _event):
        self.entry.configure(fg=THEME["fg"])
        self.error_label.configure(text="")
        self.title("Custom Playlist")

    def _paste(self):
        try:
            text = self.clipboard_get().strip()
            if text:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, text)
                self._on_key(None)
        except tk.TclError:
            pass

    def _ok(self):
        value = self.entry.get().strip()
        if not value:
            self.destroy()
            return
        if value.startswith(("http://", "https://", "rtmp://", "rtsp://")):
            self.result = value
            self.destroy()
            return
        self.entry.configure(fg=THEME["error_fg"])
        self.error_label.configure(text="Enter a valid http(s) playlist URL.")
        self.title("Custom Playlist")

    def _cancel(self):
        self.destroy()

import tkinter as tk
from tkinter import ttk
from tvwhere.config import THEME, FONTS

def set_bg_recursive(widget, color):
    """Recursively set the background color of a widget and its children."""
    try:
        # Skip buttons, badges, entries, or specific widgets where bg shouldn't change
        if not getattr(widget, '_skip_hover_bg', False):
            widget.configure(bg=color)
    except Exception:
        pass
    for child in widget.winfo_children():
        set_bg_recursive(child, color)

class ScrollableFrame(tk.Frame):
    """A pure Tkinter vertical scrollable frame container."""
    def __init__(self, parent, *args, **kwargs):
        # Apply theme colors
        kwargs['bg'] = kwargs.get('bg', THEME['bg'])
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(
            self, 
            bg=THEME['bg'], 
            highlightthickness=0, 
            borderwidth=0
        )
        self.scrollbar = tk.Scrollbar(
            self, 
            orient="vertical", 
            command=self.canvas.yview,
            bg=THEME['bg'],
            troughcolor=THEME['scrollbar'],
            bd=0,
            width=10
        )
        
        self.inner_frame = tk.Frame(self.canvas, bg=THEME['bg'])
        
        self.inner_frame_id = self.canvas.create_window(
            (0, 0), 
            window=self.inner_frame, 
            anchor="nw"
        )

        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Scroll bindings
        self.bind_mousewheel(self)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Match inner frame width to canvas width
        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def bind_mousewheel(self, widget):
        widget.bind("<Enter>", self._bind_all)
        widget.bind("<Leave>", self._unbind_all)
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _bind_all(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_all(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # Cross-platform mouse wheel handling
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        """Remove all widgets inside the scrollable container."""
        for child in self.inner_frame.winfo_children():
            child.destroy()


class SearchEntry(tk.Frame):
    """Custom search input field with placeholder support."""
    def __init__(self, parent, placeholder="Search channels...", on_change=None, *args, **kwargs):
        super().__init__(parent, bg=THEME['border'], bd=1, *args, **kwargs)
        self.placeholder = placeholder
        self.on_change = on_change

        self.entry_frame = tk.Frame(self, bg=THEME['search_bg'])
        self.entry_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_write)

        self.entry = tk.Entry(
            self.entry_frame,
            textvariable=self.var,
            bg=THEME['search_bg'],
            fg=THEME['fg'],
            insertbackground=THEME['fg'],
            font=FONTS['search'],
            bd=0,
            relief="flat"
        )
        self.entry.pack(fill="both", expand=True, padx=8, pady=6)

        # Placeholder implementation
        self.placeholder_active = True
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=THEME['fg_dim'])

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_write(self, *args):
        if not self.placeholder_active and self.on_change:
            self.on_change(self.var.get())

    def _on_focus_in(self, event):
        if self.placeholder_active:
            self.placeholder_active = False
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=THEME['fg'])

    def _on_focus_out(self, event):
        if not self.entry.get():
            self.placeholder_active = True
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=THEME['fg_dim'])

    def get_text(self) -> str:
        if self.placeholder_active:
            return ""
        return self.var.get().strip()

    def clear(self):
        self.var.set("")
        self._on_focus_out(None)


class ChannelCard(tk.Frame):
    """Clickable, hover-active channel card item."""
    def __init__(self, parent, name, group, logo, resolution, is_fav, on_click, on_fav_toggle, *args, **kwargs):
        super().__init__(parent, bg=THEME['bg_card'], cursor="hand2", *args, **kwargs)
        self.name = name
        self.group = group
        self.logo = logo
        self.resolution = resolution
        self.is_fav = is_fav
        self.on_click = on_click
        self.on_fav_toggle = on_fav_toggle

        # Accent border highlight on hover
        self.pack_propagate(False)
        self.configure(height=48)

        # Main wrapper frame to give clean padding
        self.content = tk.Frame(self, bg=THEME['bg_card'])
        self.content.pack(fill="both", expand=True, padx=12, pady=6)

        # Favorite Star Icon Label
        self.star_text = "★" if self.is_fav else "☆"
        self.star_color = THEME['fg_accent'] if self.is_fav else THEME['fg_dim']
        self.star_label = tk.Label(
            self.content,
            text=self.star_text,
            bg=THEME['bg_card'],
            fg=self.star_color,
            font=("Noto Sans", 12),
            cursor="hand2"
        )
        self.star_label._skip_hover_bg = True
        self.star_label.pack(side="left", padx=(0, 10))
        self.star_label.bind("<Button-1>", self._on_star_click)

        # Channel Name
        self.name_label = tk.Label(
            self.content,
            text=self.name,
            bg=THEME['bg_card'],
            fg=THEME['fg'],
            font=FONTS['body'],
            anchor="w"
        )
        self.name_label.pack(side="left", fill="both", expand=True)

        # Badge Frame for right-aligned items
        self.badges_frame = tk.Frame(self.content, bg=THEME['bg_card'])
        self.badges_frame.pack(side="right")

        # Resolution Badge
        if self.resolution:
            self.res_label = tk.Label(
                self.badges_frame,
                text=self.resolution.upper(),
                bg=THEME['badge_bg'],
                fg=THEME['fg_accent'],
                font=FONTS['small'],
                padx=4,
                pady=1
            )
            self.res_label._skip_hover_bg = True
            self.res_label.pack(side="right", padx=(6, 0))

        # Group Badge
        if self.group and self.group != "General":
            clean_group = self.group[:12] + ".." if len(self.group) > 14 else self.group
            self.group_label = tk.Label(
                self.badges_frame,
                text=clean_group.upper(),
                bg=THEME['badge_bg'],
                fg=THEME['fg_dim'],
                font=FONTS['small'],
                padx=6,
                pady=1
            )
            self.group_label._skip_hover_bg = True
            self.group_label.pack(side="right")

        # Bind events for entire widget tree (except star)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_card_click)

        for child in self.content.winfo_children():
            if child != self.star_label:
                child.bind("<Enter>", self._on_enter)
                child.bind("<Leave>", self._on_leave)
                child.bind("<Button-1>", self._on_card_click)

    def _on_star_click(self, event):
        self.is_fav = not self.is_fav
        self.star_text = "★" if self.is_fav else "☆"
        self.star_color = THEME['fg_accent'] if self.is_fav else THEME['fg_dim']
        self.star_label.configure(text=self.star_text, fg=self.star_color)
        if self.on_fav_toggle:
            self.on_fav_toggle(self.is_fav)
        return "break"  # Prevent propagating event to card click

    def _on_card_click(self, event):
        if self.on_click:
            self.on_click()

    def _on_enter(self, event):
        set_bg_recursive(self, THEME['bg_hover'])

    def _on_leave(self, event):
        set_bg_recursive(self, THEME['bg_card'])


class SidebarButton(tk.Frame):
    """Left sidebar tab selection buttons."""
    def __init__(self, parent, icon, text, on_click, *args, **kwargs):
        super().__init__(parent, bg=THEME['bg_secondary'], cursor="hand2", *args, **kwargs)
        self.on_click = on_click
        self.is_active = False

        self.pack_propagate(False)
        self.configure(height=42)

        # Active indicator strip on left
        self.indicator = tk.Frame(self, bg=THEME['bg_secondary'], width=3)
        self.indicator.pack(side="left", fill="y")

        # Content frame
        self.content = tk.Frame(self, bg=THEME['bg_secondary'])
        self.content.pack(side="left", fill="both", expand=True, padx=12)

        self.label = tk.Label(
            self.content,
            text=f"{icon}   {text}",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_dim'],
            font=FONTS['heading'],
            anchor="w"
        )
        self.label.pack(fill="both", expand=True)

        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_button_click)
        self.label.bind("<Enter>", self._on_enter)
        self.label.bind("<Leave>", self._on_leave)
        self.label.bind("<Button-1>", self._on_button_click)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.configure(bg=THEME['bg_active'])
            set_bg_recursive(self.content, THEME['bg_active'])
            self.indicator.configure(bg=THEME['fg_accent'])
            self.label.configure(fg=THEME['fg'])
        else:
            self.configure(bg=THEME['bg_secondary'])
            set_bg_recursive(self.content, THEME['bg_secondary'])
            self.indicator.configure(bg=THEME['bg_secondary'])
            self.label.configure(fg=THEME['fg_dim'])

    def _on_button_click(self, event):
        if self.on_click:
            self.on_click()

    def _on_enter(self, event):
        if not self.is_active:
            self.configure(bg=THEME['bg_hover'])
            set_bg_recursive(self.content, THEME['bg_hover'])

    def _on_leave(self, event):
        if not self.is_active:
            self.configure(bg=THEME['bg_secondary'])
            set_bg_recursive(self.content, THEME['bg_secondary'])


class StatusBar(tk.Frame):
    """Footer displaying playback details and total channels."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg=THEME['bg_secondary'], bd=0, *args, **kwargs)

        self.left_label = tk.Label(
            self,
            text="Ready",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_dim'],
            font=FONTS['small'],
            padx=12,
            pady=6
        )
        self.left_label.pack(side="left")

        self.right_label = tk.Label(
            self,
            text="0 channels",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_dim'],
            font=FONTS['small'],
            padx=12,
            pady=6
        )
        self.right_label.pack(side="right")

    def set_status(self, text: str):
        self.left_label.configure(text=text)

    def set_count(self, count: int):
        self.right_label.configure(text=f"{count} channels")


class LoadingIndicator(tk.Label):
    """Simple text animated loading dot indicator."""
    def __init__(self, parent, *args, **kwargs):
        kwargs['bg'] = kwargs.get('bg', THEME['bg'])
        kwargs['fg'] = kwargs.get('fg', THEME['fg_dim'])
        kwargs['font'] = kwargs.get('font', FONTS['body'])
        super().__init__(parent, text="Fetching channel list", *args, **kwargs)
        self.dots = 0
        self.running = False

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False

    def _animate(self):
        if not self.running:
            return
        self.dots = (self.dots + 1) % 4
        dots_str = "." * self.dots
        self.configure(text=f"Fetching channel list{dots_str}")
        self.after(500, self._animate)

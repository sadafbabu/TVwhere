import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox

from pathlib import Path

from tvwhere.config import (
    THEME,
    PLAYLISTS,
    PAGE_SIZE,
    SEARCH_DEBOUNCE_MS,
    SIDEBAR_TABS,
    FONTS,
    FavoritesManager,
    SettingsManager,
    ensure_dirs,
)
from tvwhere.history import HistoryManager
from tvwhere.icons import apply_window_icon, load_logo
from tvwhere.iptv import get_channels_async, clear_playlist_cache, load_m3u_from_path
from tvwhere.player import PlayerManager
from tvwhere.search import filter_channels, sort_channels
from tvwhere.service import PlaylistService
from tvwhere.widgets import (
    ScrollableFrame,
    SearchEntry,
    ChannelCard,
    SidebarButton,
    StatusBar,
    LoadingIndicator,
    EmptyState,
    UrlDialog,
)


class TVwhereApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TVwhere")
        self.root.geometry("960x640")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(720, 480)
        self._set_window_icon()

        ensure_dirs()
        self.player = PlayerManager()

        self.channels = []
        self.displayed = []
        self.active_tab = None
        self.current_playlist = SettingsManager.get_last_tab()
        self.active_group = "All"
        self._group_names = ["All"]
        self._render_offset = 0
        self._fav_names = set()
        self._search_job = None
        self._empty_state = None
        self._load_generation = 0
        self._custom_loaded = False
        self._custom_url = ""
        self._web_server = None

        self._setup_layout()
        self._bind_shortcuts()
        self._select_tab(self.current_playlist)

    def _set_window_icon(self):
        self._icon = apply_window_icon(self.root)

    def _bind_shortcuts(self):
        self.root.bind("<Control-f>", self._focus_search)
        self.root.bind("<Control-F>", self._focus_search)
        self.root.bind("<Control-r>", self._refresh_current)
        self.root.bind("<Control-R>", self._refresh_current)
        self.root.bind("<Escape>", self._on_escape)

    def _focus_search(self, _event=None):
        self.search_entry.focus()
        return "break"

    def _on_escape(self, _event=None):
        if self.search_entry.get_text():
            self.search_entry.clear()
            self._apply_filters()
            return "break"
        return None

    def _refresh_current(self, _event=None):
        if self.active_tab == "Favorites":
            self._load_favorites()
        elif self.active_tab == "Recent":
            self._load_recent()
        elif self.active_tab == "Custom URL" and self._custom_loaded:
            self._reload_custom()
        elif self.active_tab in PLAYLISTS:
            self._load_playlist(self.active_tab, force=True)
        return "break"

    def _setup_layout(self):
        self.sidebar = tk.Frame(self.root, bg=THEME["bg_secondary"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header = tk.Frame(self.sidebar, bg=THEME["bg_secondary"], pady=14)
        header.pack(fill="x")

        self._logo = load_logo(26)
        if self._logo:
            tk.Label(header, image=self._logo, bg=THEME["bg_secondary"]).pack(
                side="left", padx=(14, 6)
            )
        tk.Label(
            header,
            text="TVwhere",
            bg=THEME["bg_secondary"],
            fg=THEME["fg"],
            font=FONTS["title"],
        ).pack(side="left")

        self.sidebar_buttons = {}
        for name in SIDEBAR_TABS:
            btn = SidebarButton(
                self.sidebar,
                text=name,
                on_click=lambda n=name: self._select_tab(n),
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.sidebar_buttons[name] = btn

        web_btn = tk.Label(
            self.sidebar,
            text="Web UI (mobile)",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            cursor="hand2",
            pady=6,
        )
        web_btn.pack(side="bottom", fill="x")
        web_btn.bind("<Button-1>", lambda e: self._start_web_ui())
        web_btn.bind("<Enter>", lambda e: web_btn.configure(fg=THEME["fg"]))
        web_btn.bind("<Leave>", lambda e: web_btn.configure(fg=THEME["fg_dim"]))

        refresh_btn = tk.Label(
            self.sidebar,
            text="Refresh",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            cursor="hand2",
            pady=4,
        )
        refresh_btn.pack(side="bottom", fill="x")
        refresh_btn.bind("<Button-1>", lambda e: self._refresh_current())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.configure(fg=THEME["fg"]))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.configure(fg=THEME["fg_dim"]))

        tk.Label(
            self.sidebar,
            text=f"Player: {self.player.player_name}",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            pady=8,
        ).pack(side="bottom", fill="x")

        tk.Frame(self.root, bg=THEME["border"], width=1).pack(side="left", fill="y")

        self.main_content = tk.Frame(self.root, bg=THEME["bg"])
        self.main_content.pack(side="right", fill="both", expand=True)

        search_row = tk.Frame(self.main_content, bg=THEME["bg"], pady=10, padx=14)
        search_row.pack(fill="x")

        self.search_entry = SearchEntry(
            search_row,
            on_change=self._on_search_change,
            on_escape=self._on_escape,
        )
        self.search_entry.pack(fill="x")

        group_row = tk.Frame(self.main_content, bg=THEME["bg"], padx=14, pady=(0, 6))
        group_row.pack(fill="x")
        tk.Label(
            group_row,
            text="Group",
            bg=THEME["bg"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
        ).pack(side="left", padx=(0, 8))
        self.group_var = tk.StringVar(value="All")
        self.group_menu = tk.OptionMenu(group_row, self.group_var, "All", command=self._on_group_change)
        self.group_menu.configure(
            bg=THEME["bg_card"],
            fg=THEME["fg"],
            activebackground=THEME["bg_hover"],
            activeforeground=THEME["fg"],
            highlightthickness=0,
            borderwidth=0,
            font=FONTS["small"],
        )
        self.group_menu["menu"].configure(bg=THEME["bg_card"], fg=THEME["fg"])
        self.group_menu.pack(side="left")

        self.list_container = tk.Frame(self.main_content, bg=THEME["bg"])
        self.list_container.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        self.scroll_frame = ScrollableFrame(
            self.list_container,
            on_near_bottom=self._load_more_channels,
        )
        self.scroll_frame.pack(fill="both", expand=True)

        self.loading = LoadingIndicator(self.list_container)
        self.status_bar = StatusBar(self.main_content)
        self.status_bar.pack(side="bottom", fill="x")

    def _start_web_ui(self):
        if self._web_server:
            webbrowser.open("http://127.0.0.1:8765")
            return

        def run():
            from tvwhere.api import run_server

            run_server(host="0.0.0.0", port=8765)

        self._web_server = threading.Thread(target=run, daemon=True)
        self._web_server.start()
        self.root.after(800, lambda: webbrowser.open("http://127.0.0.1:8765"))
        self.status_bar.set_status("Web UI started — use phone on same Wi-Fi")

    def _refresh_fav_names(self):
        self._fav_names = set(FavoritesManager.load().keys())

    def _select_tab(self, tab_name):
        if self.active_tab == tab_name and tab_name != "Custom URL":
            return

        for name, btn in self.sidebar_buttons.items():
            btn.set_active(name == tab_name)

        self.active_tab = tab_name
        self.search_entry.clear()
        self.active_group = "All"
        self.group_var.set("All")

        if tab_name == "Favorites":
            self._set_group_menu_enabled(False)
            self._load_favorites()
        elif tab_name == "Recent":
            self._set_group_menu_enabled(False)
            self._load_recent()
        elif tab_name == "Custom URL":
            self._set_group_menu_enabled(True)
            if self._custom_loaded and self.channels:
                self._rebuild_groups(self.channels)
                self._apply_filters()
                self.status_bar.set_status("Custom playlist")
                self.status_bar.set_count(len(self.channels))
            else:
                self._prompt_custom_url()
        else:
            self._set_group_menu_enabled(True)
            SettingsManager.set_last_tab(tab_name)
            self._load_playlist(tab_name)

    def _set_group_menu_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.group_menu.configure(state=state)

    def _rebuild_groups(self, channels):
        groups = sorted({ch.get("group") or "General" for ch in channels}, key=str.lower)
        menu = self.group_menu["menu"]
        menu.delete(0, "end")
        self._group_names = ["All"] + groups
        for g in self._group_names:
            menu.add_command(label=g, command=lambda v=g: self._set_group(v))

    def _set_group(self, name):
        self.active_group = name
        self.group_var.set(name)
        self._apply_filters()

    def _on_group_change(self, value):
        self.active_group = value
        self._apply_filters()

    def _next_generation(self) -> int:
        self._load_generation += 1
        return self._load_generation

    def _load_playlist(self, name, force: bool = False):
        url = PLAYLISTS.get(name)
        if not url:
            return

        if force:
            clear_playlist_cache(url)

        self.current_playlist = name
        gen = self._next_generation()
        self._show_loading(True, f"Loading {name}")
        self.scroll_frame.clear()
        self._hide_empty()
        self.status_bar.set_status(f"Loading {name}...")

        def on_ok(channels, from_cache=False, g=gen):
            self.root.after(0, self._on_playlist_loaded, channels, from_cache, g)

        def on_err(err, g=gen):
            self.root.after(0, self._on_playlist_error, err, g)

        get_channels_async(url, callback=on_ok, error_callback=on_err)

    def _on_playlist_loaded(self, channels, from_cache=False, generation=0):
        if generation != self._load_generation:
            return

        self.channels = sort_channels(channels)
        self._rebuild_groups(self.channels)
        self._show_loading(False)
        self._apply_filters()

        if from_cache:
            self.status_bar.set_status("Ready (cached)")
        elif self.active_tab == "Favorites":
            self.status_bar.set_status("Favorites")
        elif self.active_tab == "Recent":
            self.status_bar.set_status("Recent")
        else:
            self.status_bar.set_status("Ready")

    def _on_playlist_error(self, error_msg, generation=0):
        if generation != self._load_generation:
            return

        self._show_loading(False)
        self.scroll_frame.clear()
        self._show_empty("Could not load playlist", error_msg)
        self.status_bar.set_status("Error")
        self.status_bar.set_count(0)
        messagebox.showerror("Playlist Error", error_msg)

    def _load_favorites(self):
        self._show_loading(False)
        self.scroll_frame.clear()
        favs = sort_channels(FavoritesManager.get_all())
        self.channels = favs
        if not favs:
            self._show_empty(
                "No favorites yet",
                "Click the star on any channel to save it here.",
            )
            self.status_bar.set_status("Favorites")
            self.status_bar.set_count(0)
            return
        self._hide_empty()
        self._apply_filters()
        self.status_bar.set_status("Favorites")

    def _load_recent(self):
        self._show_loading(False)
        self.scroll_frame.clear()
        recent = HistoryManager.get_all()
        self.channels = recent
        if not recent:
            self._show_empty("No recent channels", "Channels you play will appear here.")
            self.status_bar.set_status("Recent")
            self.status_bar.set_count(0)
            return
        self._hide_empty()
        self._apply_filters()
        self.status_bar.set_status("Recent")

    def _prompt_custom_url(self):
        dialog = UrlDialog(self.root)
        self.root.wait_window(dialog)
        url = dialog.result

        if not url:
            prev = self.current_playlist or SettingsManager.get_last_tab()
            self._custom_loaded = False
            for name, btn in self.sidebar_buttons.items():
                btn.set_active(name == prev)
            self.active_tab = prev
            if prev == "Favorites":
                self._load_favorites()
            elif prev == "Recent":
                self._load_recent()
            elif prev in PLAYLISTS:
                self._load_playlist(prev)
            return

        self._custom_url = url
        self._custom_loaded = True
        self.current_playlist = None
        self._reload_custom()

    def _reload_custom(self):
        gen = self._next_generation()
        self._show_loading(True, "Loading custom playlist")
        self.scroll_frame.clear()
        self._hide_empty()
        self.status_bar.set_status("Loading custom playlist...")

        local = Path(self._custom_url).expanduser()
        if local.is_file():
            def worker():
                try:
                    channels = sort_channels(load_m3u_from_path(str(local)))
                    self.root.after(0, self._on_custom_loaded, channels, False, gen)
                except Exception as exc:
                    self.root.after(0, self._on_playlist_error, str(exc), gen)

            threading.Thread(target=worker, daemon=True).start()
            return

        clear_playlist_cache(self._custom_url)

        def on_ok(channels, from_cache=False, g=gen):
            self.root.after(0, self._on_custom_loaded, channels, from_cache, g)

        def on_err(err, g=gen):
            self.root.after(0, self._on_playlist_error, err, g)

        get_channels_async(self._custom_url, callback=on_ok, error_callback=on_err)

    def _on_custom_loaded(self, channels, from_cache=False, generation=0):
        if generation != self._load_generation:
            return
        self._on_playlist_loaded(channels, from_cache, generation)
        self.status_bar.set_status("Custom playlist (cached)" if from_cache else "Custom playlist")

    def _show_loading(self, show: bool, message: str = "Loading channels"):
        if show:
            self.scroll_frame.pack_forget()
            self._hide_empty()
            self.loading.set_message(message)
            self.loading.pack(expand=True, fill="both")
            self.loading.start()
        else:
            self.loading.stop()
            self.loading.pack_forget()
            self.scroll_frame.pack(fill="both", expand=True)

    def _show_empty(self, title: str, subtitle: str):
        self._hide_empty()
        self._empty_state = EmptyState(self.list_container, title, subtitle)
        self._empty_state.pack(expand=True, fill="both")

    def _hide_empty(self):
        if self._empty_state:
            self._empty_state.destroy()
            self._empty_state = None

    def _apply_filters(self):
        query = self.search_entry.get_text()
        filtered = PlaylistService.search(
            self.channels,
            query,
            None if self.active_group == "All" else self.active_group,
        )
        self._display_channels(filtered)
        self.status_bar.set_count(len(filtered))
        if query.strip():
            self.status_bar.set_status(f'Search: "{query.strip()}"')

    def _display_channels(self, channel_list):
        self.displayed = list(channel_list)
        self._render_offset = 0
        self._refresh_fav_names()
        self.scroll_frame.clear()
        self._hide_empty()

        if not self.displayed:
            query = self.search_entry.get_text()
            if query:
                self._show_empty("No results", f'Nothing matched "{query}".')
            else:
                self._show_empty("No channels", "This playlist is empty.")
            self.status_bar.set_count(0)
            return

        self._append_channel_batch()

    def _append_channel_batch(self):
        if self._render_offset >= len(self.displayed):
            return

        end = min(self._render_offset + PAGE_SIZE, len(self.displayed))
        batch = self.displayed[self._render_offset : end]

        for ch in batch:
            is_fav = ch["name"] in self._fav_names
            card = ChannelCard(
                self.scroll_frame.inner_frame,
                name=ch["name"],
                group=ch.get("group", "General"),
                resolution=ch.get("resolution", ""),
                logo=ch.get("logo", ""),
                is_fav=is_fav,
                on_click=lambda c=ch: self._play_channel(c),
                on_fav_toggle=lambda state, c=ch: self._toggle_favorite(c, state),
                on_hover=lambda n=ch["name"]: self.status_bar.set_status(n),
            )
            card.pack(fill="x", pady=1)

        self._render_offset = end
        self.scroll_frame.bind_mousewheel(self.scroll_frame)

        total = len(self.displayed)
        shown = self._render_offset
        if shown < total:
            self.status_bar.set_status(f"Showing {shown} of {total}")

    def _load_more_channels(self):
        if self._render_offset < len(self.displayed):
            self._append_channel_batch()

    def _play_channel(self, channel):
        PlaylistService.record_play(channel)
        self.status_bar.set_status(f"Opening: {channel['name']}")
        success = self.player.play(channel["url"], title=channel["name"])

        if success:
            self.status_bar.set_status(f"Playing: {channel['name']}")
        else:
            self.status_bar.set_status("No player found")
            messagebox.showerror(
                "Player Required",
                "Install mpv (recommended) or VLC to play streams.\n\n"
                "Windows: winget install mpv\n"
                "macOS:   brew install mpv\n"
                "Linux:   sudo pacman -S mpv  (or apt install mpv)\n\n"
                "Or use Web UI: tvwhere --web --open",
            )

    def _toggle_favorite(self, channel, is_fav):
        if is_fav:
            FavoritesManager.add(
                channel["name"],
                channel["url"],
                channel.get("group", "General"),
                channel.get("logo", ""),
            )
            self._fav_names.add(channel["name"])
        else:
            FavoritesManager.remove(channel["name"])
            self._fav_names.discard(channel["name"])

        if self.active_tab == "Favorites":
            self.root.after(80, self._load_favorites)

    def _on_search_change(self, query):
        if self._search_job:
            self.root.after_cancel(self._search_job)
        captured = query
        self._search_job = self.root.after(
            SEARCH_DEBOUNCE_MS,
            lambda q=captured: self._apply_search(q),
        )

    def _apply_search(self, query):
        self._search_job = None
        self._apply_filters()

    def on_close(self):
        if self._search_job:
            self.root.after_cancel(self._search_job)
        self.player.stop()
        self.root.destroy()

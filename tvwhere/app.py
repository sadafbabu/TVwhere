import tkinter as tk
from tkinter import messagebox

from tvwhere.config import (
    THEME,
    PLAYLISTS,
    PAGE_SIZE,
    SEARCH_DEBOUNCE_MS,
    SIDEBAR_TABS,
    FONTS,
    FavoritesManager,
    ensure_dirs,
)
from tvwhere.icons import apply_window_icon, load_logo
from tvwhere.iptv import get_channels_async
from tvwhere.player import PlayerManager
from tvwhere.search import filter_channels
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
        self.root.geometry("920x620")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(720, 480)
        self._set_window_icon()

        ensure_dirs()
        self.player = PlayerManager()

        self.channels = []
        self.displayed = []
        self.active_tab = None
        self.current_playlist = "Bangladesh"
        self._render_offset = 0
        self._fav_names = set()
        self._search_job = None
        self._empty_state = None

        self._setup_layout()
        self._select_tab("Bangladesh")

    def _set_window_icon(self):
        self._icon = apply_window_icon(self.root)

    def _setup_layout(self):
        self.sidebar = tk.Frame(self.root, bg=THEME["bg_secondary"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header = tk.Frame(self.sidebar, bg=THEME["bg_secondary"], pady=14)
        header.pack(fill="x")

        self._logo = load_logo(26)
        if self._logo:
            tk.Label(header, image=self._logo, bg=THEME["bg_secondary"]).pack(side="left", padx=(14, 6))
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

        player_name = self.player.player_name
        tk.Label(
            self.sidebar,
            text=f"Player: {player_name}",
            bg=THEME["bg_secondary"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
            pady=10,
        ).pack(side="bottom", fill="x")

        tk.Frame(self.root, bg=THEME["border"], width=1).pack(side="left", fill="y")

        self.main_content = tk.Frame(self.root, bg=THEME["bg"])
        self.main_content.pack(side="right", fill="both", expand=True)

        search_row = tk.Frame(self.main_content, bg=THEME["bg"], pady=10, padx=14)
        search_row.pack(fill="x")

        self.search_entry = SearchEntry(search_row, on_change=self._on_search_change)
        self.search_entry.pack(fill="x")

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

    def _refresh_fav_names(self):
        self._fav_names = set(FavoritesManager.load().keys())

    def _select_tab(self, tab_name):
        if self.active_tab == tab_name and tab_name != "Custom URL":
            return

        for name, btn in self.sidebar_buttons.items():
            btn.set_active(name == tab_name)

        self.active_tab = tab_name
        self.search_entry.clear()

        if tab_name == "Favorites":
            self._load_favorites()
        elif tab_name == "Custom URL":
            self._prompt_custom_url()
        else:
            self._load_playlist(tab_name)

    def _load_playlist(self, name):
        url = PLAYLISTS.get(name)
        if not url:
            return

        self.current_playlist = name
        self._show_loading(True)
        self.scroll_frame.clear()
        self._hide_empty()
        self.status_bar.set_status(f"Loading {name}...")

        get_channels_async(
            url,
            callback=lambda ch: self.root.after(0, self._on_playlist_loaded, ch),
            error_callback=lambda err: self.root.after(0, self._on_playlist_error, err),
        )

    def _on_playlist_loaded(self, channels):
        self.channels = channels
        self._show_loading(False)
        self._display_channels(self.channels)
        self.status_bar.set_status("Ready")
        self.status_bar.set_count(len(channels))

    def _on_playlist_error(self, error_msg):
        self._show_loading(False)
        self.scroll_frame.clear()
        self._show_empty("Could not load playlist", error_msg)
        self.status_bar.set_status("Error")
        self.status_bar.set_count(0)
        messagebox.showerror("Playlist Error", error_msg)

    def _load_favorites(self):
        self._show_loading(False)
        self.scroll_frame.clear()
        favs = FavoritesManager.get_all()
        self.channels = favs
        if not favs:
            self._show_empty("No favorites yet", "Star a channel to save it here.")
            self.status_bar.set_status("Favorites")
            self.status_bar.set_count(0)
            return
        self._hide_empty()
        self._display_channels(favs)
        self.status_bar.set_status("Favorites")
        self.status_bar.set_count(len(favs))

    def _prompt_custom_url(self):
        dialog = UrlDialog(self.root)
        self.root.wait_window(dialog)
        url = dialog.result

        if not url:
            self._select_tab(self.current_playlist or "Bangladesh")
            return

        self.current_playlist = None
        self._show_loading(True)
        self.scroll_frame.clear()
        self._hide_empty()
        self.status_bar.set_status("Loading custom playlist...")

        get_channels_async(
            url,
            callback=lambda ch: self.root.after(0, self._on_playlist_loaded, ch),
            error_callback=lambda err: self.root.after(0, self._on_playlist_error, err),
        )

    def _show_loading(self, show: bool):
        if show:
            self.scroll_frame.pack_forget()
            self._hide_empty()
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
                is_fav=is_fav,
                on_click=lambda c=ch: self._play_channel(c),
                on_fav_toggle=lambda state, c=ch: self._toggle_favorite(c, state),
            )
            card.pack(fill="x", pady=1)

        self._render_offset = end
        self.scroll_frame.bind_mousewheel(self.scroll_frame)

        total = len(self.displayed)
        shown = self._render_offset
        if shown < total:
            self.status_bar.set_status(f"Showing {shown} of {total}")
        elif self.active_tab == "Favorites":
            self.status_bar.set_status("Favorites")
        else:
            self.status_bar.set_status("Ready")

    def _load_more_channels(self):
        if self._render_offset < len(self.displayed):
            self._append_channel_batch()

    def _play_channel(self, channel):
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
                "Linux:   sudo pacman -S mpv  (or apt install mpv)",
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
        self._search_job = self.root.after(
            SEARCH_DEBOUNCE_MS,
            lambda: self._apply_search(query),
        )

    def _apply_search(self, query):
        self._search_job = None
        filtered = filter_channels(self.channels, query)
        self._display_channels(filtered)
        self.status_bar.set_count(len(filtered))
        if query.strip():
            self.status_bar.set_status(f'Search: "{query.strip()}"')

    def on_close(self):
        if self._search_job:
            self.root.after_cancel(self._search_job)
        self.player.stop()
        self.root.destroy()

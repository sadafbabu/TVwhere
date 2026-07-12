import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox

from pathlib import Path

from tvwhere.config import (
    THEME,
    PAGE_SIZE,
    SEARCH_DEBOUNCE_MS,
    AUTO_REFRESH_MINUTES,
    SIDEBAR_TABS,
    FONTS,
    FavoritesManager,
    SettingsManager,
    ensure_dirs,
)
from tvwhere.countries import COUNTRIES, LANGUAGES, get_name
from tvwhere.history import HistoryManager
from tvwhere.icons import apply_window_icon, load_logo
from tvwhere.iptv import clear_playlist_cache, load_m3u_from_path
from tvwhere.player import PlayerManager
from tvwhere.search import sort_channels
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
        self.root.geometry("980x660")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(760, 500)
        self._set_window_icon()

        ensure_dirs()
        self.player = PlayerManager()

        self.channels = []
        self.displayed = []
        self.active_tab = None
        self.country_code = SettingsManager.get_country()
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
        self._channel_fp = ""
        self._silent_refresh_job = None
        self._status_flash_job = None

        self._setup_layout()
        self._bind_shortcuts()
        last = SettingsManager.get_last_tab()
        if last in SIDEBAR_TABS:
            self._select_tab(last)
        else:
            self._show_channels()
        self._schedule_silent_refresh()

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
            self._reload_custom(force=True)
        elif self.active_tab == "channels":
            self._load_country(self.country_code, force=True)
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
        title_label = tk.Label(
            header,
            text="TVwhere",
            bg=THEME["bg_secondary"],
            fg=THEME["fg"],
            font=FONTS["title"],
            cursor="hand2",
        )
        title_label.pack(side="left")
        title_label.bind("<Button-1>", lambda e: self._show_channels())

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

        country_row = tk.Frame(self.main_content, bg=THEME["bg"], padx=14, pady=10)
        country_row.pack(fill="x")
        tk.Label(
            country_row,
            text="Country",
            bg=THEME["bg"],
            fg=THEME["fg_dim"],
            font=FONTS["small"],
        ).pack(side="left", padx=(0, 8))
        self.country_var = tk.StringVar(value=self._country_label(self.country_code))
        labels = []
        self._country_by_name = {}
        for c in COUNTRIES:
            labels.append(c["name"])
            self._country_by_name[c["name"]] = c["code"]
        for lang in LANGUAGES:
            label = f"Language: {lang['name']}"
            labels.append(label)
            self._country_by_name[label] = lang["code"]
        self.country_menu = tk.OptionMenu(
            country_row,
            self.country_var,
            *labels,
            command=self._on_country_change,
        )
        self.country_menu.configure(
            bg=THEME["bg_card"],
            fg=THEME["fg"],
            activebackground=THEME["bg_hover"],
            activeforeground=THEME["fg"],
            highlightthickness=0,
            borderwidth=0,
            font=FONTS["small"],
        )
        self.country_menu["menu"].configure(bg=THEME["bg_card"], fg=THEME["fg"])
        self.country_menu.pack(side="left", fill="x", expand=True)

        search_row = tk.Frame(self.main_content, bg=THEME["bg"], pady=6, padx=14)
        search_row.pack(fill="x")

        self.search_entry = SearchEntry(
            search_row,
            on_change=self._on_search_change,
            on_escape=self._on_escape,
        )
        self.search_entry.pack(fill="x")

        group_row = tk.Frame(self.main_content, bg=THEME["bg"], padx=14, pady=6)
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

    def _country_label(self, code: str) -> str:
        for lang in LANGUAGES:
            if lang["code"] == code:
                return f"Language: {lang['name']}"
        return get_name(code)

    def _set_country_menu_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.country_menu.configure(state=state)

    def _on_country_change(self, name):
        code = self._country_by_name.get(name, self.country_code)
        if code == self.country_code:
            return
        self.country_code = code
        SettingsManager.set_country(code)
        if self.active_tab == "channels":
            self._load_country(code)

    def _show_channels(self):
        for name, btn in self.sidebar_buttons.items():
            btn.set_active(False)
        self.active_tab = "channels"
        self.search_entry.clear()
        self.active_group = "All"
        self.group_var.set("All")
        self._set_group_menu_enabled(True)
        self._set_country_menu_enabled(True)
        SettingsManager.set_last_tab("channels")
        self._load_country(self.country_code)

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
        if tab_name not in SIDEBAR_TABS:
            self._show_channels()
            return
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
            self._set_country_menu_enabled(False)
            self._load_favorites()
        elif tab_name == "Recent":
            self._set_group_menu_enabled(False)
            self._set_country_menu_enabled(False)
            self._load_recent()
        elif tab_name == "Custom URL":
            self._set_group_menu_enabled(True)
            self._set_country_menu_enabled(False)
            if self._custom_loaded and self.channels:
                self._rebuild_groups(self.channels)
                self._apply_filters()
                self.status_bar.set_status("Custom playlist")
                self.status_bar.set_count(len(self.displayed))
            else:
                self._prompt_custom_url()
        SettingsManager.set_last_tab(tab_name)

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

    def _load_country(self, code: str, force: bool = False, silent: bool = False):
        from tvwhere.countries import get_url

        url = get_url(code)
        if force:
            clear_playlist_cache(url)

        gen = self._next_generation()
        if not silent:
            self._show_loading(True, get_name(code))
            self.scroll_frame.clear()
            self._hide_empty()
            self.status_bar.set_status(f"Loading {get_name(code)}...")

        def worker():
            try:
                channels = PlaylistService.load_country_channels(code, force=force)
                self.root.after(0, self._on_channels_ready, channels, False, gen, silent)
            except Exception as exc:
                self.root.after(0, self._on_playlist_error, str(exc), gen)

        threading.Thread(target=worker, daemon=True).start()

    def _on_channels_ready(self, channels, from_cache=False, generation=0, silent=False):
        if generation != self._load_generation:
            return

        channels = sort_channels(channels)
        new_fp = PlaylistService.fingerprint(channels)

        if silent and new_fp == self._channel_fp:
            self._flash_status("Up to date")
            return

        scroll_pos = None
        if silent and self._channel_fp:
            try:
                scroll_pos = self.scroll_frame.canvas.yview()[0]
            except Exception:
                pass

        self.channels = channels
        self._channel_fp = new_fp
        self._rebuild_groups(self.channels)

        if not silent:
            self._show_loading(False)

        self._apply_filters(preserve_scroll=scroll_pos)

        if silent:
            self._flash_status("Updated" if not from_cache else "Updated (cached)")
        elif from_cache:
            self.status_bar.set_status("Ready (cached)")
        else:
            self.status_bar.set_status(f"Ready — {get_name(self.country_code)}")

        PlaylistService.start_health_checks(
            self.channels,
            on_dead=lambda: self.root.after(0, self._on_health_prune),
            on_done=lambda _: self.root.after(0, self._on_health_prune),
        )

    def _on_health_prune(self):
        if self.active_tab not in ("channels", "Custom URL"):
            return
        scroll_pos = None
        try:
            scroll_pos = self.scroll_frame.canvas.yview()[0]
        except Exception:
            pass
        alive = PlaylistService.apply_health(self.channels)
        if len(alive) == len(self.displayed):
            return
        self.channels = alive
        self._channel_fp = PlaylistService.fingerprint(alive)
        self._apply_filters(preserve_scroll=scroll_pos)

    def _on_playlist_error(self, error_msg, generation=0):
        if generation != self._load_generation:
            return
        self._show_loading(False)
        self.scroll_frame.clear()
        self._show_empty("Could not load playlist", error_msg)
        self.status_bar.set_status("Error")
        self.status_bar.set_count(0)
        if "silent" not in error_msg.lower():
            messagebox.showerror("Playlist Error", error_msg)

    def _load_favorites(self):
        self._show_loading(False)
        self.scroll_frame.clear()
        favs = sort_channels(FavoritesManager.get_all())
        self.channels = favs
        self._channel_fp = PlaylistService.fingerprint(favs)
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
        self._channel_fp = PlaylistService.fingerprint(recent)
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
            prev = SettingsManager.get_last_tab()
            self._custom_loaded = False
            for name, btn in self.sidebar_buttons.items():
                btn.set_active(name == prev)
            self.active_tab = prev
            self._select_tab(prev)
            return

        self._custom_url = url
        self._custom_loaded = True
        self._reload_custom()

    def _reload_custom(self, force: bool = False):
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
                    self.root.after(0, self._on_channels_ready, channels, False, gen, False)
                except Exception as exc:
                    self.root.after(0, self._on_playlist_error, str(exc), gen)

            threading.Thread(target=worker, daemon=True).start()
            return

        if force:
            clear_playlist_cache(self._custom_url)

        def worker():
            try:
                from tvwhere.iptv import fetch_and_parse

                result = {"channels": None, "err": None}

                def ok(ch, **_):
                    result["channels"] = ch

                def err(e):
                    result["err"] = e

                fetch_and_parse(self._custom_url, ok, err)
                if result["err"]:
                    self.root.after(0, self._on_playlist_error, result["err"], gen)
                else:
                    self.root.after(
                        0, self._on_channels_ready, sort_channels(result["channels"]), False, gen, False
                    )
            except Exception as exc:
                self.root.after(0, self._on_playlist_error, str(exc), gen)

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_silent_refresh(self):
        if self._silent_refresh_job:
            self.root.after_cancel(self._silent_refresh_job)
        ms = AUTO_REFRESH_MINUTES * 60 * 1000
        self._silent_refresh_job = self.root.after(ms, self._silent_refresh_tick)

    def _silent_refresh_tick(self):
        if self.active_tab == "channels":
            self._load_country(self.country_code, force=False, silent=True)
        self._schedule_silent_refresh()

    def _flash_status(self, text: str, ms: int = 2500):
        if self._status_flash_job:
            self.root.after_cancel(self._status_flash_job)
        self.status_bar.set_status(text)
        self._status_flash_job = self.root.after(ms, lambda: self.status_bar.set_status("Ready"))

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

    def _apply_filters(self, preserve_scroll=None):
        query = self.search_entry.get_text()
        filtered = PlaylistService.search(
            self.channels,
            query,
            None if self.active_group == "All" else self.active_group,
        )
        if self.active_tab in ("channels", "Custom URL", "Favorites", "Recent"):
            filtered = PlaylistService.apply_health(filtered)
        self._display_channels(filtered, preserve_scroll=preserve_scroll)
        self.status_bar.set_count(len(filtered))
        if query.strip():
            self.status_bar.set_status(f'Search: "{query.strip()}"')

    def _display_channels(self, channel_list, preserve_scroll=None):
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
                self._show_empty("No channels", "No working channels found for this filter.")
            self.status_bar.set_count(0)
            return

        self._append_channel_batch()
        if preserve_scroll is not None:
            self.root.after(50, lambda: self.scroll_frame.canvas.yview_moveto(preserve_scroll))

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
        self._search_job = self.root.after(SEARCH_DEBOUNCE_MS, self._apply_search)

    def _apply_search(self):
        self._search_job = None
        self._apply_filters()

    def on_close(self):
        if self._search_job:
            self.root.after_cancel(self._search_job)
        if self._silent_refresh_job:
            self.root.after_cancel(self._silent_refresh_job)
        self.player.stop()
        self.root.destroy()

import tkinter as tk
from tkinter import messagebox, simpledialog
from tvwhere.config import THEME, PLAYLISTS, FavoritesManager, ensure_dirs
from tvwhere.iptv import get_channels_async
from tvwhere.player import PlayerManager
from tvwhere.widgets import (
    ScrollableFrame, SearchEntry, ChannelCard, 
    SidebarButton, StatusBar, LoadingIndicator
)

class TVwhereApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TVwhere")
        self.root.geometry("900x600")
        self.root.configure(bg=THEME['bg'])
        self.root.minsize(700, 450)

        # Initialize Managers
        ensure_dirs()
        self.player = PlayerManager()
        
        # State Variables
        self.channels = []          # Master channel list for active playlist
        self.active_tab = None      # Current sidebar tab
        self.current_playlist = None # Currently loaded playlist name
        
        self._setup_layout()
        self._setup_styles()
        
        # Load default tab
        self._select_tab("Bangladesh")

    def _setup_layout(self):
        # 1. Sidebar Frame
        self.sidebar = tk.Frame(self.root, bg=THEME['bg_secondary'], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App Logo / Title
        self.logo_label = tk.Label(
            self.sidebar,
            text="TVwhere",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_accent'],
            font=("Noto Sans", 18, "bold"),
            pady=20
        )
        self.logo_label.pack(fill="x")

        # Sidebar Navigation Buttons
        self.sidebar_buttons = {}
        tabs = [
            ("🇧🇩", "Bangladesh"),
            ("🌐", "Bengali"),
            ("🌍", "Global"),
            ("⭐", "Favorites"),
            ("⚙️", "Custom URL")
        ]
        
        for emoji, name in tabs:
            btn = SidebarButton(
                self.sidebar,
                icon=emoji,
                text=name,
                on_click=lambda n=name: self._select_tab(n)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.sidebar_buttons[name] = btn

        # Detected Player Info in Sidebar footer
        self.player_label = tk.Label(
            self.sidebar,
            text=f"Player: {self.player.player_name.upper()}",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_dim'],
            font=("Noto Sans", 8),
            pady=12
        )
        self.player_label.pack(side="bottom", fill="x")

        # Divider between sidebar and main content
        self.divider = tk.Frame(self.root, bg=THEME['border'], width=1)
        self.divider.pack(side="left", fill="y")

        # 2. Main Content Frame
        self.main_content = tk.Frame(self.root, bg=THEME['bg'])
        self.main_content.pack(side="right", fill="both", expand=True)

        # Search Bar Area
        self.search_frame = tk.Frame(self.main_content, bg=THEME['bg'], pady=12, padx=16)
        self.search_frame.pack(fill="x")
        
        self.search_entry = SearchEntry(
            self.search_frame,
            on_change=self._on_search_change
        )
        self.search_entry.pack(fill="x")

        # Main Channel List Area
        self.list_container = tk.Frame(self.main_content, bg=THEME['bg'])
        self.list_container.pack(fill="both", expand=True, padx=16)

        self.scroll_frame = ScrollableFrame(self.list_container)
        self.scroll_frame.pack(fill="both", expand=True)

        # Loading Indicator
        self.loading = LoadingIndicator(self.list_container)
        
        # Status Bar
        self.status_bar = StatusBar(self.main_content)
        self.status_bar.pack(side="bottom", fill="x")

    def _setup_styles(self):
        # Configure Tkinter standard font and styles if needed
        pass

    def _select_tab(self, tab_name):
        if self.active_tab == tab_name and tab_name != "Custom URL":
            return
            
        # Update active sidebar highlight
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
        
        # Set status bar
        self.status_bar.set_status(f"Loading {name} channels...")
        
        # Call IPTV parser in background thread
        get_channels_async(
            url,
            callback=lambda ch: self.root.after(0, self._on_playlist_loaded, ch),
            error_callback=lambda err: self.root.after(0, self._on_playlist_error, err)
        )

    def _on_playlist_loaded(self, channels):
        self.channels = channels
        self._show_loading(False)
        self._display_channels(self.channels)
        self.status_bar.set_status("Ready")
        self.status_bar.set_count(len(channels))

    def _on_playlist_error(self, error_msg):
        self._show_loading(False)
        self.status_bar.set_status("Failed to load playlist.")
        messagebox.showerror("Error", error_msg)

    def _load_favorites(self):
        self._show_loading(False)
        self.scroll_frame.clear()
        favs = FavoritesManager.get_all()
        self.channels = favs
        self._display_channels(favs)
        self.status_bar.set_status("Viewing Favorites")
        self.status_bar.set_count(len(favs))

    def _prompt_custom_url(self):
        # Open simple tkinter input dialog
        url = simpledialog.askstring("Custom Playlist", "Enter custom M3U playlist URL:")
        if not url:
            # Revert to last active tab
            if self.current_playlist:
                self._select_tab(self.current_playlist)
            return

        self._show_loading(True)
        self.scroll_frame.clear()
        self.status_bar.set_status("Loading custom playlist...")

        get_channels_async(
            url,
            callback=lambda ch: self.root.after(0, self._on_playlist_loaded, ch),
            error_callback=lambda err: self.root.after(0, self._on_playlist_error, err)
        )

    def _show_loading(self, show: bool):
        if show:
            self.scroll_frame.pack_forget()
            self.loading.pack(expand=True, fill="both")
            self.loading.start()
        else:
            self.loading.stop()
            self.loading.pack_forget()
            self.scroll_frame.pack(fill="both", expand=True)

    def _display_channels(self, channel_list):
        self.scroll_frame.clear()
        
        # Build cards
        for ch in channel_list:
            is_fav = FavoritesManager.is_favorite(ch['name'])
            card = ChannelCard(
                self.scroll_frame.inner_frame,
                name=ch['name'],
                group=ch.get('group', 'General'),
                logo=ch.get('logo', ''),
                resolution=ch.get('resolution', ''),
                is_fav=is_fav,
                on_click=lambda c=ch: self._play_channel(c),
                on_fav_toggle=lambda state, c=ch: self._toggle_favorite(c, state)
            )
            card.pack(fill="x", pady=2)
            
        # Re-bind mousewheel to new widgets
        self.scroll_frame.bind_mousewheel(self.scroll_frame)

    def _play_channel(self, channel):
        self.status_bar.set_status(f"Buffering: {channel['name']}...")
        success = self.player.play(channel['url'], title=channel['name'])
        
        if success:
            self.status_bar.set_status(f"Playing: {channel['name']}")
        else:
            self.status_bar.set_status("Playback failed. No player found.")
            messagebox.showerror(
                "Player Error", 
                "Neither mpv nor vlc was detected on your system.\n"
                "Please install mpv or vlc to play streams."
            )

    def _toggle_favorite(self, channel, is_fav):
        if is_fav:
            FavoritesManager.add(
                channel['name'], 
                channel['url'], 
                channel.get('group', 'General'),
                channel.get('logo', '')
            )
        else:
            FavoritesManager.remove(channel['name'])
            
        # If currently viewing Favorites, refresh view
        if self.active_tab == "Favorites":
            self.root.after(100, self._load_favorites)

    def _on_search_change(self, query):
        if not query:
            self._display_channels(self.channels)
            self.status_bar.set_count(len(self.channels))
            return
            
        # Filter channel list
        query = query.lower()
        filtered = [
            ch for ch in self.channels 
            if query in ch['name'].lower() or query in ch.get('group', '').lower()
        ]
        self._display_channels(filtered)
        self.status_bar.set_count(len(filtered))

    def on_close(self):
        """Cleanup player resources on window exit."""
        self.player.stop()
        self.root.destroy()

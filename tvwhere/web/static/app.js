const state = {
  view: "playlist",
  playlistId: null,
  channels: [],
  favorites: new Set(),
  playingUrl: null,
  hls: null,
  debounce: null,
};

const $ = (sel) => document.querySelector(sel);
const playlistList = $("#playlistList");
const channelList = $("#channelList");
const searchInput = $("#searchInput");
const groupSelect = $("#groupSelect");
const playerPanel = $("#playerPanel");
const video = $("#video");
const nowPlaying = $("#nowPlaying");
const loading = $("#loading");
const emptyState = $("#emptyState");
const modal = $("#modal");

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function logoUrl(url) {
  if (!url) return "";
  return `/api/logo?url=${encodeURIComponent(url)}`;
}

function streamUrl(url) {
  return `/api/stream?url=${encodeURIComponent(url)}`;
}

async function loadPlaylists() {
  const { playlists } = await api("/api/playlists");
  playlistList.innerHTML = "";
  playlists.forEach((pl) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = pl.name;
    btn.dataset.id = pl.id;
    if (pl.id === state.playlistId) btn.classList.add("active");
    btn.onclick = () => selectPlaylist(pl.id);
    li.appendChild(btn);
    playlistList.appendChild(li);
  });
  if (!state.playlistId && playlists.length) {
    selectPlaylist(playlists[0].id);
  }
}

async function loadFavorites() {
  const { channels } = await api("/api/favorites");
  state.favorites = new Set(channels.map((c) => c.name));
  return channels;
}

async function loadChannels(refresh = false) {
  loading.classList.remove("hidden");
  emptyState.classList.add("hidden");
  channelList.innerHTML = "";
  try {
    let channels = [];
    if (state.view === "favorites") {
      channels = await loadFavorites();
    } else if (state.view === "recent") {
      const res = await api("/api/recent");
      channels = res.channels;
    } else if (state.playlistId) {
      const group = groupSelect.value;
      const q = searchInput.value.trim();
      const qs = new URLSearchParams();
      if (group) qs.set("group", group);
      if (q) qs.set("q", q);
      if (refresh) qs.set("refresh", "1");
      const res = await api(`/api/playlists/${state.playlistId}/channels?${qs}`);
      channels = res.channels;
      if (!group && !q) await loadGroups();
    }
    state.channels = channels;
    renderChannels(channels);
  } catch (err) {
    emptyState.textContent = err.message;
    emptyState.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
  }
}

async function loadGroups() {
  if (!state.playlistId || state.view !== "playlist") return;
  try {
    const { groups } = await api(`/api/playlists/${state.playlistId}/groups`);
    const current = groupSelect.value;
    groupSelect.innerHTML = '<option value="">All groups</option>';
    groups.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = g.name;
      opt.textContent = `${g.name} (${g.count})`;
      groupSelect.appendChild(opt);
    });
    groupSelect.value = current;
  } catch (_) {}
}

function renderChannels(channels) {
  channelList.innerHTML = "";
  if (!channels.length) {
    emptyState.textContent = "No channels found";
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");
  channels.forEach((ch) => {
    const row = document.createElement("div");
    row.className = "channel" + (state.playingUrl === ch.url ? " playing" : "");

    if (ch.logo) {
      const img = document.createElement("img");
      img.src = logoUrl(ch.logo);
      img.alt = "";
      img.loading = "lazy";
      row.appendChild(img);
    } else {
      const ph = document.createElement("div");
      ph.className = "logo-placeholder";
      ph.textContent = "TV";
      row.appendChild(ph);
    }

    const info = document.createElement("div");
    info.className = "info";
    const name = document.createElement("div");
    name.className = "name";
    name.textContent = ch.name;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = [ch.group, ch.resolution].filter(Boolean).join(" · ");
    info.appendChild(name);
    info.appendChild(meta);
    row.appendChild(info);

    const star = document.createElement("button");
    star.className = "star" + (state.favorites.has(ch.name) ? " on" : "");
    star.textContent = state.favorites.has(ch.name) ? "★" : "☆";
    star.onclick = (e) => {
      e.stopPropagation();
      toggleFavorite(ch, star);
    };
    row.appendChild(star);

    row.onclick = () => playChannel(ch);
    channelList.appendChild(row);
  });
}

async function toggleFavorite(ch, btn) {
  const on = btn.classList.toggle("on");
  btn.textContent = on ? "★" : "☆";
  if (on) {
    state.favorites.add(ch.name);
    await api("/api/favorites", { method: "POST", body: JSON.stringify({ channel: ch }) });
  } else {
    state.favorites.delete(ch.name);
    await api(`/api/favorites/${encodeURIComponent(ch.name)}`, { method: "DELETE" });
  }
}

function playChannel(ch) {
  state.playingUrl = ch.url;
  nowPlaying.textContent = ch.name;
  playerPanel.classList.remove("hidden");
  renderChannels(state.channels);
  api("/api/play", { method: "POST", body: JSON.stringify({ channel: ch }) });

  const src = streamUrl(ch.url);
  if (state.hls) {
    state.hls.destroy();
    state.hls = null;
  }
  video.removeAttribute("src");
  video.load();

  if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = src;
    video.play().catch(() => {});
  } else if (window.Hls && Hls.isSupported()) {
    state.hls = new Hls({ enableWorker: true, lowLatencyMode: true });
    state.hls.loadSource(src);
    state.hls.attachMedia(video);
    state.hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
  } else {
    video.src = ch.url;
    video.play().catch(() => {});
  }
}

function selectPlaylist(id) {
  state.view = "playlist";
  state.playlistId = id;
  document.querySelectorAll("#playlistList button").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === id);
  });
  document.querySelectorAll(".nav-list button").forEach((b) => b.classList.remove("active"));
  groupSelect.disabled = false;
  loadChannels();
  closeSidebar();
}

function selectView(view) {
  state.view = view;
  state.playlistId = null;
  document.querySelectorAll("#playlistList button").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".nav-list button").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  groupSelect.disabled = true;
  loadChannels();
  closeSidebar();
}

function openModal() {
  modal.classList.remove("hidden");
  $("#modalError").textContent = "";
}
function closeModal() {
  modal.classList.add("hidden");
}

function closeSidebar() {
  $("#sidebar").classList.remove("open");
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const name = tab.dataset.tab;
    $("#tabM3u").classList.toggle("hidden", name !== "m3u");
    $("#tabXtream").classList.toggle("hidden", name !== "xtream");
  };
});

$("#menuBtn").onclick = () => $("#sidebar").classList.toggle("open");
$("#addBtn").onclick = openModal;
$("#modalCancel").onclick = closeModal;
$("#refreshBtn").onclick = () => loadChannels(true);
$("#extPlayBtn").onclick = () => {
  if (state.playingUrl) window.open(state.playingUrl, "_blank");
};

searchInput.oninput = () => {
  clearTimeout(state.debounce);
  state.debounce = setTimeout(() => loadChannels(), 180);
};
groupSelect.onchange = () => loadChannels();

$("#modalSave").onclick = async () => {
  const activeTab = document.querySelector(".tab.active").dataset.tab;
  try {
    if (activeTab === "m3u") {
      await api("/api/playlists", {
        method: "POST",
        body: JSON.stringify({
          type: "m3u",
          name: $("#m3uName").value,
          url: $("#m3uUrl").value,
          epg_url: $("#epgUrl").value,
        }),
      });
    } else {
      await api("/api/playlists", {
        method: "POST",
        body: JSON.stringify({
          type: "xtream",
          name: $("#xcName").value,
          server: $("#xcServer").value,
          username: $("#xcUser").value,
          password: $("#xcPass").value,
        }),
      });
    }
    closeModal();
    await loadPlaylists();
    loadChannels();
  } catch (err) {
    $("#modalError").textContent = err.message;
  }
};

document.querySelectorAll(".nav-list button").forEach((btn) => {
  btn.onclick = () => selectView(btn.dataset.view);
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

loadFavorites().then(loadPlaylists);

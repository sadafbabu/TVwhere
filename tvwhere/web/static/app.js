const AUTO_REFRESH_MS = 45 * 60 * 1000;
const HEALTH_POLL_MS = 90 * 1000;

const state = {
  view: "live",
  country: "global",
  playlistId: null,
  channels: [],
  fingerprint: "",
  favorites: new Set(),
  playingUrl: null,
  hls: null,
  debounce: null,
  silentTimer: null,
  healthTimer: null,
  busy: false,
};

const $ = (sel) => document.querySelector(sel);
const playlistList = $("#playlistList");
const channelList = $("#channelList");
const searchInput = $("#searchInput");
const groupSelect = $("#groupSelect");
const countrySelect = $("#countrySelect");
const resolutionSelect = $("#resolutionSelect");
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

function clearNavActive() {
  document.querySelectorAll("#playlistList button").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".nav-list button").forEach((b) => b.classList.remove("active"));
}

function setToolbarForView() {
  const isLive = state.view === "live";
  countrySelect.disabled = !isLive;
  groupSelect.disabled = state.view === "favorites" || state.view === "recent";
  resolutionSelect.disabled = state.view === "favorites" || state.view === "recent";
}

function populateCountrySelect(regions, selected) {
  countrySelect.innerHTML = "";
  regions.countries.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.code;
    opt.textContent = c.name;
    opt.selected = c.code === selected;
    countrySelect.appendChild(opt);
  });
  const langGroup = document.createElement("optgroup");
  langGroup.label = "Languages";
  regions.languages.forEach((l) => {
    const opt = document.createElement("option");
    opt.value = l.code;
    opt.textContent = l.name;
    opt.selected = l.code === selected;
    langGroup.appendChild(opt);
  });
  countrySelect.appendChild(langGroup);
}

async function loadFavorites() {
  const { channels } = await api("/api/favorites");
  state.favorites = new Set(channels.map((c) => c.name));
  return channels;
}

async function loadPlaylists() {
  const { playlists } = await api("/api/playlists");
  playlistList.innerHTML = "";
  playlists.forEach((pl) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = pl.name;
    btn.dataset.id = pl.id;
    if (state.view === "playlist" && pl.id === state.playlistId) btn.classList.add("active");
    btn.onclick = () => selectPlaylist(pl.id);
    li.appendChild(btn);
    playlistList.appendChild(li);
  });
}

function buildQuery(refresh) {
  const qs = new URLSearchParams();
  const group = groupSelect.value;
  const q = searchInput.value.trim();
  const res = resolutionSelect.value;
  if (state.view === "live") qs.set("country", state.country);
  if (group) qs.set("group", group);
  if (q) qs.set("q", q);
  if (res) qs.set("resolution", res);
  if (refresh) qs.set("refresh", "1");
  return qs;
}

async function loadGroups() {
  if (state.view === "live") {
    const qs = new URLSearchParams({ country: state.country });
    const { groups } = await api(`/api/live/groups?${qs}`);
    fillGroupSelect(groups);
    return;
  }
  if (state.view === "playlist" && state.playlistId) {
    const { groups } = await api(`/api/playlists/${state.playlistId}/groups`);
    fillGroupSelect(groups);
  }
}

function fillGroupSelect(groups) {
  const current = groupSelect.value;
  groupSelect.innerHTML = '<option value="">All groups</option>';
  groups.forEach((g) => {
    const opt = document.createElement("option");
    opt.value = g.name;
    opt.textContent = `${g.name} (${g.count})`;
    groupSelect.appendChild(opt);
  });
  groupSelect.value = current;
}

async function loadChannels(refresh = false, silent = false) {
  if (state.busy && silent) return;
  state.busy = true;

  if (!silent) {
    loading.classList.remove("hidden");
    emptyState.classList.add("hidden");
    channelList.innerHTML = "";
  }

  try {
    let channels = [];
    if (state.view === "favorites") {
      channels = await loadFavorites();
    } else if (state.view === "recent") {
      const res = await api("/api/recent");
      channels = res.channels;
    } else if (state.view === "live") {
      const qs = buildQuery(refresh);
      const res = await api(`/api/live/channels?${qs}`);
      channels = res.channels;
      if (res.fingerprint) state.fingerprint = res.fingerprint;
      if (!silent && !searchInput.value.trim() && !groupSelect.value) await loadGroups();
    } else if (state.playlistId) {
      const qs = buildQuery(refresh);
      const res = await api(`/api/playlists/${state.playlistId}/channels?${qs}`);
      channels = res.channels;
      if (!silent && !searchInput.value.trim() && !groupSelect.value) await loadGroups();
    }
    state.channels = channels;
    renderChannels(channels);
  } catch (err) {
    if (!silent) {
      emptyState.textContent = err.message;
      emptyState.classList.remove("hidden");
    }
  } finally {
    if (!silent) loading.classList.add("hidden");
    state.busy = false;
  }
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
    meta.textContent = [ch.radio ? "Radio" : null, ch.group, ch.resolution]
      .filter(Boolean)
      .join(" · ");
    if (ch.resolution && ch.resolution.toUpperCase() === "4K") {
      name.style.color = "#e8e8e8";
    }
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

async function loadEpg(ch) {
  if (!state.playlistId || !ch.id) return;
  try {
    const epg = await api(
      `/api/epg?playlist=${encodeURIComponent(state.playlistId)}&channel=${encodeURIComponent(ch.id)}`
    );
    let text = ch.name;
    if (epg.now && epg.now.title) {
      text += ` — Now: ${epg.now.title}`;
      if (epg.next && epg.next.title) text += ` | Next: ${epg.next.title}`;
    }
    nowPlaying.textContent = text;
  } catch (_) {}
}

function stopPlayback() {
  if (state.hls) {
    state.hls.destroy();
    state.hls = null;
  }
  video.pause();
  video.removeAttribute("src");
  video.load();
  state.playingUrl = null;
  playerPanel.classList.add("hidden");
  renderChannels(state.channels);
}

function playChannel(ch) {
  state.playingUrl = ch.url;
  nowPlaying.textContent = ch.name;
  playerPanel.classList.remove("hidden");
  renderChannels(state.channels);
  api("/api/play", { method: "POST", body: JSON.stringify({ channel: ch }) });
  loadEpg(ch);

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

function selectLive() {
  state.view = "live";
  state.playlistId = null;
  clearNavActive();
  setToolbarForView();
  loadChannels();
  closeSidebar();
}

function selectPlaylist(id) {
  state.view = "playlist";
  state.playlistId = id;
  clearNavActive();
  document.querySelectorAll("#playlistList button").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === id);
  });
  setToolbarForView();
  groupSelect.value = "";
  loadChannels();
  closeSidebar();
}

function selectView(view) {
  state.view = view;
  state.playlistId = null;
  clearNavActive();
  document.querySelectorAll(".nav-list button").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  setToolbarForView();
  groupSelect.value = "";
  loadChannels();
  closeSidebar();
}

async function silentRefresh() {
  if (state.view !== "live" || state.busy) return;
  try {
    const qs = new URLSearchParams({ country: state.country, refresh: "1" });
    const res = await api(`/api/live/channels?${qs}`);
    if (res.fingerprint && res.fingerprint !== state.fingerprint) {
      state.fingerprint = res.fingerprint;
      await loadChannels(false, true);
    }
  } catch (_) {}
}

function scheduleTimers() {
  if (state.silentTimer) clearInterval(state.silentTimer);
  state.silentTimer = setInterval(silentRefresh, AUTO_REFRESH_MS);

  if (state.healthTimer) clearInterval(state.healthTimer);
  state.healthTimer = setInterval(() => {
    if (state.view === "live" && !state.busy && !state.playingUrl) {
      loadChannels(false, true);
    }
  }, HEALTH_POLL_MS);
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
$("#homeBtn").onclick = () => selectLive();
$("#modalCancel").onclick = closeModal;
$("#refreshBtn").onclick = () => loadChannels(true);
$("#stopBtn").onclick = () => stopPlayback();

countrySelect.onchange = async () => {
  state.country = countrySelect.value;
  await api("/api/settings", {
    method: "POST",
    body: JSON.stringify({ country: state.country }),
  });
  groupSelect.value = "";
  loadChannels();
};

searchInput.oninput = () => {
  clearTimeout(state.debounce);
  state.debounce = setTimeout(() => loadChannels(), 180);
};
groupSelect.onchange = () => loadChannels();
resolutionSelect.onchange = async () => {
  await api("/api/settings", {
    method: "POST",
    body: JSON.stringify({ resolution: resolutionSelect.value }),
  });
  loadChannels();
};

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
    const last = playlistList.querySelector("button:last-child");
    if (last) selectPlaylist(last.dataset.id);
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

async function init() {
  const [settings, regions] = await Promise.all([
    api("/api/settings"),
    api("/api/countries"),
  ]);
  state.country = settings.country || "global";
  if (settings.resolution) resolutionSelect.value = settings.resolution;
  populateCountrySelect(regions, state.country);
  await loadFavorites();
  await loadPlaylists();
  selectLive();
  scheduleTimers();

  const params = new URLSearchParams(location.search);
  const autoplay = params.get("autoplay");
  if (autoplay) {
    const ch = { name: "Stream", url: decodeURIComponent(autoplay), group: "", resolution: "" };
    setTimeout(() => playChannel(ch), 500);
  }
}

init();

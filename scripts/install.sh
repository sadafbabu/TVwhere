#!/usr/bin/env bash
# Install TVwhere launcher, desktop entry, and fix local permissions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME="$(eval echo "~${REAL_USER}")"

BIN_DIR="${REAL_HOME}/.local/bin"
APP_DIR="${REAL_HOME}/.local/share/applications"
CONFIG_DIR="${REAL_HOME}/.config/tvwhere"
CACHE_DIR="${REAL_HOME}/.cache/tvwhere"

mkdir -p "$BIN_DIR" "$APP_DIR" "$CONFIG_DIR" "$CACHE_DIR"

# Editable install (optional — Arch may block pip; launcher uses PYTHONPATH)
if sudo -u "$REAL_USER" pip install --user -e "$ROOT" --quiet 2>/dev/null; then
  :
elif pip install --user -e "$ROOT" --quiet 2>/dev/null; then
  :
else
  echo "Note: pip install skipped (using PYTHONPATH launcher instead)."
fi

# Desktop app launcher (opens window)
cat > "${BIN_DIR}/tvwhere" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${ROOT}:\${PYTHONPATH:-}"
cd "${ROOT}"
exec python3 -m tvwhere "\$@" || exec python -m tvwhere "\$@"
EOF
chmod +x "${BIN_DIR}/tvwhere"

# Web/mobile server launcher
cat > "${BIN_DIR}/tvwhere-web" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${ROOT}:\${PYTHONPATH:-}"
cd "${ROOT}"
exec python3 -m tvwhere --web --open "\$@" || exec python -m tvwhere --web --open "\$@"
EOF
chmod +x "${BIN_DIR}/tvwhere-web"

ICON="${ROOT}/assets/icon.png"

cat > "${APP_DIR}/tvwhere.desktop" <<EOF
[Desktop Entry]
Version=2.2
Type=Application
Name=TVwhere
GenericName=IPTV Player
Comment=Cross-platform IPTV Player
Exec=env PYTHONPATH=${ROOT} python3 -m tvwhere --desktop
Icon=${ICON}
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=tv;iptv;live;stream;
StartupWMClass=tvwhere
EOF

cat > "${APP_DIR}/tvwhere-web.desktop" <<EOF
[Desktop Entry]
Version=2.0
Type=Application
Name=TVwhere Web
GenericName=IPTV Web Player
Comment=TVwhere web UI for mobile and browser
Exec=env PYTHONPATH=${ROOT} python3 -m tvwhere --web --open
Icon=${ICON}
Terminal=true
Categories=AudioVideo;Video;Player;Network;
Keywords=tv;iptv;mobile;pwa;
EOF

cp "${APP_DIR}/tvwhere.desktop" "${ROOT}/tvwhere.desktop"

# Fix ownership — config/cache often end up root:root after IDE agent runs
if [ -d "$CONFIG_DIR" ] || [ -d "$CACHE_DIR" ]; then
  chown -R "${REAL_USER}:${REAL_USER}" "$CONFIG_DIR" "$CACHE_DIR" 2>/dev/null || true
fi
if [ "$(id -u)" -eq 0 ] || [ "$REAL_USER" != "$USER" ]; then
  chown -R "${REAL_USER}:${REAL_USER}" \
    "$ROOT" "$BIN_DIR/tvwhere" "$BIN_DIR/tvwhere-web" \
    "$APP_DIR/tvwhere.desktop" "$APP_DIR/tvwhere-web.desktop" \
    "$CONFIG_DIR" "$CACHE_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  sudo -u "$REAL_USER" update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "TVwhere 2.0 installed."
echo "  Project   : ${ROOT}"
echo "  Desktop   : tvwhere"
echo "  Web/Mobile: tvwhere-web"
echo "  Icon      : ${ICON}"

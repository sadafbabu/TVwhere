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

# Launcher always knows project root (fallback if pip install failed)
cat > "${BIN_DIR}/tvwhere" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${ROOT}:\${PYTHONPATH:-}"
cd "${ROOT}"
exec python3 -m tvwhere "\$@" 2>/dev/null || exec python -m tvwhere "\$@"
EOF
chmod +x "${BIN_DIR}/tvwhere"

ICON="${ROOT}/assets/icon.png"

cat > "${APP_DIR}/tvwhere.desktop" <<EOF
[Desktop Entry]
Version=1.1
Type=Application
Name=TVwhere
GenericName=IPTV Player
Comment=Minimalist IPTV Player
Exec=env PYTHONPATH=${ROOT} python3 -m tvwhere
Icon=${ICON}
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=tv;iptv;live;stream;
StartupWMClass=tvwhere
EOF

cp "${APP_DIR}/tvwhere.desktop" "${ROOT}/tvwhere.desktop"

# Fix ownership if files were created as root
if [ "$(id -u)" -eq 0 ] || [ "$REAL_USER" != "$USER" ]; then
  chown -R "${REAL_USER}:${REAL_USER}" \
    "$ROOT" "$BIN_DIR/tvwhere" "$APP_DIR/tvwhere.desktop" \
    "$CONFIG_DIR" "$CACHE_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  sudo -u "$REAL_USER" update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "TVwhere installed."
echo "  Project : ${ROOT}"
echo "  Launch  : tvwhere"
echo "  Icon    : ${ICON}"

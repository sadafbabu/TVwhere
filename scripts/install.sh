#!/usr/bin/env bash
# Install TVwhere launcher + desktop entry (Linux / macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"

mkdir -p "$BIN_DIR" "$APP_DIR" "${HOME}/.config/tvwhere" "${HOME}/.cache/tvwhere"

cat > "${BIN_DIR}/tvwhere" <<EOF
#!/usr/bin/env bash
exec python3 -m tvwhere "\$@" 2>/dev/null || exec python -m tvwhere "\$@"
EOF
chmod +x "${BIN_DIR}/tvwhere"

# Ensure package is importable from project root
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"
pip install -e "$ROOT" --quiet 2>/dev/null || true

cat > "${APP_DIR}/tvwhere.desktop" <<EOF
[Desktop Entry]
Name=TVwhere
Comment=Minimalist IPTV Player
Exec=env PYTHONPATH=${ROOT} python3 -m tvwhere
Icon=${ROOT}/assets/icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Video;Player;
Keywords=tv;iptv;live;stream;
StartupWMClass=tvwhere
EOF

cp "${APP_DIR}/tvwhere.desktop" "${ROOT}/tvwhere.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "TVwhere installed."
echo "  Project : ${ROOT}"
echo "  Launch  : tvwhere"
echo "  Or      : python3 -m tvwhere  (from ${ROOT})"

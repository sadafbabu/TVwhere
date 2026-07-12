#!/usr/bin/env bash
set -euo pipefail

rm -f "${HOME}/.local/bin/tvwhere" "${HOME}/.local/share/applications/tvwhere.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
fi

echo "TVwhere launcher removed."
echo "Source kept at: $(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

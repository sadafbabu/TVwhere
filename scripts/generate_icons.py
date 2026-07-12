#!/usr/bin/env python3
"""Generate TVwhere icon assets from SVG (all sizes + Windows .ico)."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SVG = ASSETS / "icon.svg"
SOURCE_PNG = ASSETS / "icon.png"

SIZES = (16, 32, 48, 64, 128, 256)


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    if not SOURCE_PNG.is_file() and SVG.is_file():
        run(["rsvg-convert", "-w", "256", "-h", "256", "-o", str(SOURCE_PNG), str(SVG)])

    if not SOURCE_PNG.is_file():
        print("No icon source found.", file=sys.stderr)
        sys.exit(1)

    for size in SIZES:
        out = ASSETS / f"icon-{size}.png"
        run(["magick", str(SOURCE_PNG), "-resize", f"{size}x{size}", str(out)])

    # Standard names used by desktop entries
    run(["magick", str(SOURCE_PNG), "-resize", "256x256", str(ASSETS / "icon.png")])

    ico = ASSETS / "icon.ico"
    run([
        "magick", str(SOURCE_PNG),
        "-define", "icon:auto-resize=256,128,64,48,32,16",
        str(ico),
    ])

    print("Icons generated in", ASSETS)


if __name__ == "__main__":
    main()

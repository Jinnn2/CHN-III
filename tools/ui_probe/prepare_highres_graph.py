#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pcx_tmg_tool import read_pcx24, write_bmp24


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ui_probe" / "pcx_tmg_tool.py"
GRAPH_DIR = ROOT / "GRAPH"
OUT_DIR = ROOT / "ModernUIExport" / "GRAPH"

FULLSCREEN_TMG = [
    "back.TMG",
    "CAST.TMG",
    "DRAGON.TMG",
    "Loading.TMG",
    "MAINMENU.TMG",
    "MEET_EAST.TMG",
    "MEET_MODEM.TMG",
    "MEET_OLD.TMG",
    "MEET_WEST.TMG",
    "SCORELIST.TMG",
]


def cover_resize(image, width, height):
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def make_highres(source, width, height):
    stem = source.stem
    bmp_output = OUT_DIR / f"{stem}_{width}x{height}.bmp"
    tmg_output = OUT_DIR / f"{stem}_{width}x{height}{source.suffix}"

    _, old_width, old_height, _, rgb = read_pcx24(source)
    image = Image.frombytes("RGB", (old_width, old_height), rgb)
    highres = cover_resize(image, width, height)
    write_bmp24(bmp_output, width, height, highres.tobytes())
    subprocess.check_call(
        [
            sys.executable,
            str(TOOL),
            "import-any",
            str(source),
            str(bmp_output),
            str(tmg_output),
        ]
    )
    return bmp_output, tmg_output


def main():
    parser = argparse.ArgumentParser(description="Create high-resolution GRAPH fullscreen backgrounds.")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--install", action="store_true", help="Replace GRAPH files after creating backups.")
    parser.add_argument("--files", nargs="*", default=FULLSCREEN_TMG)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = ROOT / "ModernUIBackup" / f"GRAPH_{args.width}x{args.height}"
    if args.install:
        backup_dir.mkdir(parents=True, exist_ok=True)

    for name in args.files:
        source = GRAPH_DIR / name
        if not source.exists():
            print(f"skip missing: {source}")
            continue
        bmp, tmg = make_highres(source, args.width, args.height)
        print(f"created {tmg}")
        if args.install:
            backup = backup_dir / name
            if not backup.exists():
                shutil.copy2(source, backup)
            shutil.copy2(tmg, source)
            print(f"installed {source}")

    if args.install:
        print(f"backup: {backup_dir}")


if __name__ == "__main__":
    main()

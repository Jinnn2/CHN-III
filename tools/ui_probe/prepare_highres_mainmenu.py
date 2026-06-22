#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pcx_tmg_tool import read_pcx24, write_bmp24


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ui_probe" / "pcx_tmg_tool.py"
SOURCE_TMG = ROOT / "GRAPH" / "MAINMENU.TMG"
OUT_DIR = ROOT / "ModernUIExport" / "GRAPH"


def cover_resize(image, width, height):
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def main():
    parser = argparse.ArgumentParser(description="Create a high-resolution MAINMENU.TMG experiment.")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--source", default=str(SOURCE_TMG))
    parser.add_argument("--bmp-output", default="")
    parser.add_argument("--tmg-output", default="")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bmp_output = Path(args.bmp_output) if args.bmp_output else OUT_DIR / f"MAINMENU_{args.width}x{args.height}.bmp"
    tmg_output = Path(args.tmg_output) if args.tmg_output else OUT_DIR / f"MAINMENU_{args.width}x{args.height}.TMG"

    _, width, height, _, rgb = read_pcx24(args.source)
    image = Image.frombytes("RGB", (width, height), rgb)
    highres = cover_resize(image, args.width, args.height)
    write_bmp24(bmp_output, args.width, args.height, highres.tobytes())

    subprocess.check_call(
        [
            sys.executable,
            str(TOOL),
            "import-any",
            str(args.source),
            str(bmp_output),
            str(tmg_output),
        ]
    )
    print(f"wrote BMP: {bmp_output}")
    print(f"wrote TMG: {tmg_output}")


if __name__ == "__main__":
    main()

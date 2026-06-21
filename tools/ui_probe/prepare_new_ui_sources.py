#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = ROOT / "ModernUIExport" / "NEW"
GRAPH_DIR = ROOT / "ModernUIExport" / "GRAPH"

TARGETS = {
    "MAINMENU.png": ("MAINMENU.bmp", 1024, 768),
    "LOADING.png": ("Loading.bmp", 1024, 768),
}


def ps_quote(path):
    return "'" + str(path).replace("'", "''") + "'"


def convert_with_powershell(source, target, width, height):
    script = f"""
Add-Type -AssemblyName System.Drawing
$src = [System.Drawing.Image]::FromFile({ps_quote(source)})
try {{
    $bmp = New-Object System.Drawing.Bitmap {width}, {height}, ([System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    try {{
        $gfx = [System.Drawing.Graphics]::FromImage($bmp)
        try {{
            $gfx.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $gfx.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $gfx.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $gfx.DrawImage($src, 0, 0, {width}, {height})
        }} finally {{
            $gfx.Dispose()
        }}
        $bmp.Save({ps_quote(target)}, [System.Drawing.Imaging.ImageFormat]::Bmp)
    }} finally {{
        $bmp.Dispose()
    }}
}} finally {{
    $src.Dispose()
}}
"""
    subprocess.check_call(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script])


def main():
    parser = argparse.ArgumentParser(description="Convert high-resolution NEW PNG sources into importable 24-bit GRAPH BMP files.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--only", choices=sorted(TARGETS), help="Convert one source file only.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    converted = 0
    for source_name, (target_name, width, height) in TARGETS.items():
        if args.only and source_name != args.only:
            continue

        source = source_dir / source_name
        target = GRAPH_DIR / target_name
        if not source.exists():
            print(f"skip missing source: {source}")
            continue

        convert_with_powershell(source, target, width, height)
        print(f"converted {source} -> {target} ({width}x{height}, 24-bit BMP)")
        converted += 1

    print(f"done. converted {converted} file(s)")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "ModernUIExport" / "GRAPH"

EXPECTED = {
    "back.bmp": (1024, 768),
    "CAST.bmp": (1024, 768),
    "DRAGON.bmp": (1024, 768),
    "Loading.bmp": (1024, 768),
    "MAINMENU.bmp": (1024, 768),
    "MEET_EAST.bmp": (1024, 768),
    "MEET_MODEM.bmp": (1024, 768),
    "MEET_OLD.bmp": (1024, 768),
    "MEET_WEST.bmp": (1024, 768),
    "SCORELIST.bmp": (1024, 768),
    "USER_35.bmp": (640, 480),
    "USER_81.bmp": (640, 480),
}


def read_bmp_header(path):
    raw = path.read_bytes()
    if len(raw) < 54 or raw[:2] != b"BM":
        raise ValueError("not a BMP file")

    dib_size = struct.unpack_from("<I", raw, 14)[0]
    if dib_size < 40:
        raise ValueError("unsupported BMP DIB header")

    width, height, planes, bpp, compression = struct.unpack_from("<iiHHI", raw, 18)
    return width, abs(height), planes, bpp, compression


def main():
    errors = []

    if not EXPORT_DIR.exists():
        print(f"missing export folder: {EXPORT_DIR}")
        return 1

    for name, expected_size in EXPECTED.items():
        path = EXPORT_DIR / name
        if not path.exists():
            errors.append(f"{name}: missing")
            continue

        try:
            width, height, planes, bpp, compression = read_bmp_header(path)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue

        if (width, height) != expected_size:
            errors.append(f"{name}: expected {expected_size[0]}x{expected_size[1]}, got {width}x{height}")
        if planes != 1 or bpp != 24 or compression != 0:
            errors.append(f"{name}: expected uncompressed 24-bit BMP, got planes={planes}, bpp={bpp}, compression={compression}")

    if errors:
        print("validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"validation passed: {len(EXPECTED)} editable GRAPH BMP file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

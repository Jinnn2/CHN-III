#!/usr/bin/env python3
import argparse
import shutil
import struct
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "China2EX_fontfix8.exe"
DEFAULT_OUTPUT = ROOT / "China2EX_modtest_startmode2_1280x1024.exe"

MODE_INDEX_VA = 0x58940C
WIDTH_TABLE_VA = 0x589410
HEIGHT_TABLE_VA = 0x58941C
STARTUP_APPLY_PATCH_VA = 0x46EA77
STARTUP_APPLY_PATCH = bytes.fromhex("c7042402000000909090")
STARTUP_APPLY_ORIGINAL = bytes.fromhex("c7050c945800ffffffff")

MAINMENU_CENTER_PATCHES = {
    0x478EE6: "center_y",
    0x478EEB: "center_x",
    0x478F1B: "center_x",
    0x478F25: "center_y",
}

MAINMENU_ITEM_TABLE_VA = 0x575B60
MAINMENU_ITEM_RECORD_SIZE = 0x60

# The original menu item table uses fixed 1024-ish coordinates and off-screen
# animation starts. These target coordinates keep the nine menu buttons inside a
# 1280x1024 menu composition while preserving the original left/right/bottom
# grouping.
MAINMENU_1280_LAYOUT = [
    (70, 450),
    (95, 570),
    (165, 655),
    (990, 570),
    (325, 805),
    (930, 760),
    (1015, 450),
    (760, 845),
    (545, 885),
]

MAINMENU_1280_TEXT_PATCHES = {
    0x4790B0: 930,  # green version y
    0x4790B5: 820,  # green version x
    0x4790D1: 929,  # shadow version y
    0x4790D6: 819,  # shadow version x
    0x4790F8: 934,  # major version number y
    0x4790FD: 1032, # major version number x
    0x47911A: 934,  # minor version number y
    0x47911F: 1070, # minor version number x
}

MAINMENU_INITIAL_STATE_IMMEDIATE_VA = 0x478FDE


def va_to_offset(pe, va):
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def write_i32(data, offset, value):
    struct.pack_into("<i", data, offset, value)


def checked_patch_bytes(pe, data, va, old_bytes, new_bytes):
    off = va_to_offset(pe, va)
    old = bytes(data[off : off + len(new_bytes)])
    if old != old_bytes and old != new_bytes:
        raise SystemExit(
            f"unexpected original bytes at 0x{va:x}: got {old.hex()}, expected {old_bytes.hex()}"
        )
    data[off : off + len(new_bytes)] = new_bytes
    print(f"- 0x{va:x}: {old.hex()} -> {new_bytes.hex()}")


def main():
    parser = argparse.ArgumentParser(description="Patch startup to enter mode 2 immediately.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument(
        "--patch-mainmenu-layout",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Patch the hard-coded main-menu item table for the selected resolution.",
    )
    parser.add_argument(
        "--initial-screen-state",
        type=int,
        help="Optional replacement for MainMenu_Init's initial g_app_screen_state value.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    if not source.exists():
        raise SystemExit(f"missing input EXE: {source}")
    if output.exists() and not args.force:
        raise SystemExit(f"output already exists: {output}. Use --force to overwrite.")

    shutil.copy2(source, output)
    data = bytearray(output.read_bytes())
    pe = pefile.PE(data=bytes(data))

    print("patching mode table:")
    write_u32(data, va_to_offset(pe, MODE_INDEX_VA), 1)
    write_u32(data, va_to_offset(pe, WIDTH_TABLE_VA) + 2 * 4, args.width)
    write_u32(data, va_to_offset(pe, HEIGHT_TABLE_VA) + 2 * 4, args.height)
    print(f"- mode 2 -> {args.width}x{args.height}")

    print("patching startup Apply_Resolution_Mode call:")
    checked_patch_bytes(pe, data, STARTUP_APPLY_PATCH_VA, STARTUP_APPLY_ORIGINAL, STARTUP_APPLY_PATCH)

    print("patching main menu center:")
    center_x = args.width // 2
    center_y = args.height // 2
    for va, field in MAINMENU_CENTER_PATCHES.items():
        value = center_x if field == "center_x" else center_y
        off = va_to_offset(pe, va)
        old = read_u32(data, off)
        write_u32(data, off, value)
        print(f"- 0x{va:x}: {old} -> {value}")

    if args.patch_mainmenu_layout:
        if (args.width, args.height) != (1280, 1024):
            print("- skipped item-table layout patch: currently tuned only for 1280x1024")
        else:
            print("patching main menu item table:")
            for index, (x, y) in enumerate(MAINMENU_1280_LAYOUT):
                record_va = MAINMENU_ITEM_TABLE_VA + index * MAINMENU_ITEM_RECORD_SIZE
                target_x_off = va_to_offset(pe, record_va + 8)
                target_y_off = va_to_offset(pe, record_va + 12)
                current_x_off = va_to_offset(pe, record_va + 16)
                current_y_off = va_to_offset(pe, record_va + 20)

                old_x = read_u32(data, target_x_off)
                old_y = read_u32(data, target_y_off)
                write_i32(data, target_x_off, x)
                write_i32(data, target_y_off, y)

                # Preserve the original entrance direction: left-side items
                # start off the left edge, right-side items start off the right,
                # and bottom items rise from below.
                if x < args.width * 0.33:
                    start_x, start_y = -160, y
                elif x > args.width * 0.66:
                    start_x, start_y = args.width + 160, y
                else:
                    start_x, start_y = x, args.height + 80
                write_i32(data, current_x_off, start_x)
                write_i32(data, current_y_off, start_y)
                print(f"- item {index}: ({old_x},{old_y}) -> ({x},{y}), start=({start_x},{start_y})")

            print("patching main menu version text:")
            for va, value in MAINMENU_1280_TEXT_PATCHES.items():
                off = va_to_offset(pe, va)
                old = read_u32(data, off)
                write_u32(data, off, value)
                print(f"- 0x{va:x}: {old} -> {value}")

    if args.initial_screen_state is not None:
        off = va_to_offset(pe, MAINMENU_INITIAL_STATE_IMMEDIATE_VA)
        old = read_u32(data, off)
        write_u32(data, off, args.initial_screen_state)
        print(
            "patching initial screen state:"
            f"\n- 0x{MAINMENU_INITIAL_STATE_IMMEDIATE_VA:x}: {old} -> {args.initial_screen_state}"
        )

    output.write_bytes(data)
    print(f"wrote: {output}")


if __name__ == "__main__":
    main()

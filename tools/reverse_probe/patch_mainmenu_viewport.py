#!/usr/bin/env python3
import argparse
import shutil
import struct
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "China2EX_fontfix8.exe"
DEFAULT_OUTPUT = ROOT / "China2EX_modtest_1600x1200_menuviewport.exe"

MODE_INDEX_VA = 0x58940C
WIDTH_TABLE_VA = 0x589410
HEIGHT_TABLE_VA = 0x58941C

# MainMenu_Init hard-codes the 1024x768 center as 0x200/0x180 before
# loading MAINMENU.TMG and menu sprites. These addresses point to the
# immediate operands in China2EX_fontfix8.exe, image base 0x400000.
MAINMENU_PATCH_U32_BY_VA = {
    0x478EE6: 600,  # push 0x180 -> y center for call 0x48b4f0
    0x478EEB: 800,  # push 0x200 -> x center for call 0x48b4f0
    0x478F1B: 800,  # mov [0x77b1b4], 0x200
    0x478F25: 600,  # mov [0x77b1c8], 0x180
}

MAINMENU_EXPECTED_ORIGINALS = {
    0x478EE6: 0x180,
    0x478EEB: 0x200,
    0x478F1B: 0x200,
    0x478F25: 0x180,
}

# The windowed/blt DirectDraw path also hard-codes a 1024x768 present
# rectangle before creating the primary/back surfaces. If this is left at
# 1024x768, the mode table can say 1600x1200 while the visible windowed output
# still behaves like the original resolution.
WINDOWED_PRESENT_PATCH_U32_BY_VA = {
    0x4F0A5F: 1200,  # mov ebp, 0x300 -> height
    0x4F0A6F: 1600,  # mov [0x75cf10], 0x400 -> client/right point x
    0x4F0A89: 1600,  # mov eax, 0x400 -> present width / dst right
}

WINDOWED_PRESENT_EXPECTED_ORIGINALS = {
    0x4F0A5F: 0x300,
    0x4F0A6F: 0x400,
    0x4F0A89: 0x400,
}

# Startup normally calls Apply_Resolution_Mode(0, 0), which forces the game into
# the 800x600 logical path before the menu appears. At this point the two
# arguments are already on the stack; replacing the following "mode_index = -1"
# instruction with "*(uint32_t *)esp = 2" changes the pending call to
# Apply_Resolution_Mode(2, 0). The data-table mode_index is kept at 1 so the
# function does not early-return.
STARTUP_APPLY_MODE_PATCH_BY_VA = {
    0x46EA77: bytes.fromhex("c7042402000000909090"),
}

STARTUP_APPLY_MODE_EXPECTED_BY_VA = {
    0x46EA77: bytes.fromhex("c7050c945800ffffffff"),
}


def va_to_offset(pe, va):
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def patch_u32_values(pe, data, patch_values, expected_values):
    for va, value in patch_values.items():
        off = va_to_offset(pe, va)
        old = read_u32(data, off)
        expected = expected_values[va]
        if old != expected and old != value:
            raise SystemExit(
                f"unexpected original value at 0x{va:x}: got 0x{old:x}, expected 0x{expected:x}"
            )
        write_u32(data, off, value)
        print(f"- 0x{va:x}: {old} -> {value}")


def patch_bytes(pe, data, patch_values, expected_values):
    for va, value in patch_values.items():
        off = va_to_offset(pe, va)
        old = bytes(data[off : off + len(value)])
        expected = expected_values[va]
        if old != expected and old != value:
            raise SystemExit(
                f"unexpected original bytes at 0x{va:x}: got {old.hex()}, expected {expected.hex()}"
            )
        data[off : off + len(value)] = value
        print(f"- 0x{va:x}: {old.hex()} -> {value.hex()}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a 1600x1200 test EXE with the main-menu viewport center patched to 800x600."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Source EXE to copy and patch.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Patched EXE output path.")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it already exists.")
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

    print("patching resolution mode:")
    write_u32(data, va_to_offset(pe, MODE_INDEX_VA), 1)
    write_u32(data, va_to_offset(pe, WIDTH_TABLE_VA) + 2 * 4, 1600)
    write_u32(data, va_to_offset(pe, HEIGHT_TABLE_VA) + 2 * 4, 1200)
    print("- mode 2 -> 1600x1200")

    print("patching startup Apply_Resolution_Mode call:")
    patch_bytes(pe, data, STARTUP_APPLY_MODE_PATCH_BY_VA, STARTUP_APPLY_MODE_EXPECTED_BY_VA)

    print("patching main menu viewport constants:")
    patch_u32_values(pe, data, MAINMENU_PATCH_U32_BY_VA, MAINMENU_EXPECTED_ORIGINALS)

    print("patching windowed present constants:")
    patch_u32_values(
        pe,
        data,
        WINDOWED_PRESENT_PATCH_U32_BY_VA,
        WINDOWED_PRESENT_EXPECTED_ORIGINALS,
    )

    output.write_bytes(data)
    print(f"wrote: {output}")


if __name__ == "__main__":
    main()

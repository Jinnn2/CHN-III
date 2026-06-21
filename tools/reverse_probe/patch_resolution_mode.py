#!/usr/bin/env python3
import argparse
import shutil
import struct
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "China2EX_fontfix8.exe"
DEFAULT_OUTPUT = ROOT / "China2EX_modtest.exe"

MODE_INDEX_VA = 0x58940C
WIDTH_TABLE_VA = 0x589410
HEIGHT_TABLE_VA = 0x58941C
MODE_COUNT = 3


def va_to_offset(pe, va):
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def read_modes(pe, data):
    mode_index = read_u32(data, va_to_offset(pe, MODE_INDEX_VA))
    widths = [read_u32(data, va_to_offset(pe, WIDTH_TABLE_VA) + i * 4) for i in range(MODE_COUNT)]
    heights = [read_u32(data, va_to_offset(pe, HEIGHT_TABLE_VA) + i * 4) for i in range(MODE_COUNT)]
    return mode_index, widths, heights


def print_modes(label, mode_index, widths, heights):
    print(label)
    print(f"- mode_index: {mode_index}")
    for idx, (width, height) in enumerate(zip(widths, heights)):
        marker = " current" if idx == mode_index else ""
        print(f"- mode {idx}: {width}x{height}{marker}")


def main():
    parser = argparse.ArgumentParser(description="Create a test EXE with a patched internal resolution mode.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Source EXE to copy and patch.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Patched EXE output path.")
    parser.add_argument("--mode-index", type=int, default=2, choices=range(MODE_COUNT), help="Startup mode index.")
    parser.add_argument("--mode-width", type=int, help="Optionally replace the selected mode width.")
    parser.add_argument("--mode-height", type=int, help="Optionally replace the selected mode height.")
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

    old_index, old_widths, old_heights = read_modes(pe, data)
    print_modes("before:", old_index, old_widths, old_heights)

    index_off = va_to_offset(pe, MODE_INDEX_VA)
    write_u32(data, index_off, args.mode_index)

    if args.mode_width is not None or args.mode_height is not None:
        if args.mode_width is None or args.mode_height is None:
            raise SystemExit("--mode-width and --mode-height must be provided together.")
        width_off = va_to_offset(pe, WIDTH_TABLE_VA) + args.mode_index * 4
        height_off = va_to_offset(pe, HEIGHT_TABLE_VA) + args.mode_index * 4
        write_u32(data, width_off, args.mode_width)
        write_u32(data, height_off, args.mode_height)

    output.write_bytes(data)

    new_data = output.read_bytes()
    new_pe = pefile.PE(data=new_data)
    new_index, new_widths, new_heights = read_modes(new_pe, new_data)
    print_modes("after:", new_index, new_widths, new_heights)
    print(f"wrote: {output}")


if __name__ == "__main__":
    main()

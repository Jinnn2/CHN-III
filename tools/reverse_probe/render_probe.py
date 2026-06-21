#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "China2EX_fontfix8.exe"


def va_to_offset(pe, va):
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def main():
    parser = argparse.ArgumentParser(description="Probe China2 DirectDraw render and resolution-mode metadata.")
    parser.add_argument("exe", nargs="?", default=str(DEFAULT_EXE))
    args = parser.parse_args()

    exe = Path(args.exe)
    data = exe.read_bytes()
    pe = pefile.PE(str(exe))
    base = pe.OPTIONAL_HEADER.ImageBase
    print(f"exe: {exe}")
    print(f"image_base: 0x{base:x}")

    print("\nDirectDraw imports:")
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        if entry.dll.lower() == b"ddraw.dll":
            for imp in entry.imports:
                name = imp.name.decode("ascii", "replace") if imp.name else f"#{imp.ordinal}"
                print(f"- {name}: IAT 0x{imp.address:x}")

    mode_index_va = 0x58940C
    width_table_va = 0x589410
    height_table_va = 0x58941C
    mode_index = read_u32(data, va_to_offset(pe, mode_index_va))
    widths = [read_u32(data, va_to_offset(pe, width_table_va) + i * 4) for i in range(3)]
    heights = [read_u32(data, va_to_offset(pe, height_table_va) + i * 4) for i in range(3)]

    print("\nStatic resolution mode table:")
    print(f"- mode_index @ 0x{mode_index_va:x}: {mode_index}")
    for idx, (width, height) in enumerate(zip(widths, heights)):
        marker = " current" if idx == mode_index else ""
        print(f"- mode {idx}: {width}x{height}{marker}")

    print("\nKnown DirectDraw render logic sites:")
    print("- 0x46d4a3: IDirectDraw::SetCooperativeLevel call")
    print("- 0x46d4dd: IDirectDraw::CreateSurface call")
    print("- 0x4f0b1f: IDirectDraw::SetDisplayMode using mode table")
    print("- 0x4f0f69: IDirectDraw::SetDisplayMode using 0x589418/0x589424 globals")
    print("- 0x4f82a5: likely DirectDraw surface method, not display mode")

    print("\nDisassembly around primary SetDisplayMode:")
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    start_va = 0x4F0AFD
    start_off = va_to_offset(pe, start_va)
    for ins in md.disasm(data[start_off:start_off + 0x40], start_va):
        print(f"{ins.address:08x}: {ins.mnemonic:7s} {ins.op_str}")


if __name__ == "__main__":
    main()

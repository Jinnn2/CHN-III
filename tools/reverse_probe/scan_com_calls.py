#!/usr/bin/env python3
import argparse
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "China2EX_fontfix8.exe"

DIRECTDRAW_METHODS = {
    0x00: "QueryInterface",
    0x04: "AddRef",
    0x08: "Release",
    0x18: "CreateSurface",
    0x30: "GetDisplayMode",
    0x4C: "RestoreDisplayMode",
    0x50: "SetCooperativeLevel",
    0x54: "SetDisplayMode",
    0x58: "WaitForVerticalBlank",
}

SURFACE_METHODS = {
    0x00: "QueryInterface",
    0x04: "AddRef",
    0x08: "Release",
    0x14: "Blt",
    0x18: "BltBatch",
    0x1C: "BltFast",
    0x2C: "Flip",
    0x44: "GetDC",
    0x54: "GetPixelFormat",
    0x58: "GetSurfaceDesc",
    0x64: "Lock",
    0x68: "ReleaseDC",
    0x6C: "Restore",
    0x80: "Unlock",
}


def find_text_section(pe):
    for section in pe.sections:
        if section.Name.rstrip(b"\0") == b".text":
            return section
    raise SystemExit("missing .text section")


def method_name(displacement):
    dd = DIRECTDRAW_METHODS.get(displacement)
    surface = SURFACE_METHODS.get(displacement)
    if dd and surface:
        return f"DirectDraw::{dd} / Surface::{surface}"
    if dd:
        return f"DirectDraw::{dd}"
    if surface:
        return f"Surface::{surface}"
    return None


def main():
    parser = argparse.ArgumentParser(description="Scan indirect COM vtable calls in the game executable.")
    parser.add_argument("exe", nargs="?", default=str(DEFAULT_EXE))
    parser.add_argument("--markdown", action="store_true", help="Emit a Markdown table.")
    args = parser.parse_args()

    exe = Path(args.exe)
    data = exe.read_bytes()
    pe = pefile.PE(str(exe))
    base = pe.OPTIONAL_HEADER.ImageBase
    text = find_text_section(pe)
    text_data = data[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
    text_va = base + text.VirtualAddress

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    reg_names = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]
    rows = []
    i = 0
    while i < len(text_data) - 2:
        if text_data[i] != 0xFF:
            i += 1
            continue

        modrm = text_data[i + 1]
        reg_opcode = (modrm >> 3) & 0x07
        if reg_opcode != 2:
            i += 1
            continue

        mod = (modrm >> 6) & 0x03
        rm = modrm & 0x07
        disp = None
        size = None
        if mod == 1 and i + 2 < len(text_data):
            disp = text_data[i + 2]
            size = 3
        elif mod == 2 and i + 5 < len(text_data):
            disp = int.from_bytes(text_data[i + 2:i + 6], "little", signed=True)
            size = 6

        if disp is None or disp < 0:
            i += 1
            continue

        name = method_name(disp)
        if not name:
            i += 1
            continue

        address = text_va + i
        operand = f"dword ptr [{reg_names[rm]} + 0x{disp:x}]"
        try:
            insns = list(md.disasm(text_data[i:i + size], address))
            if insns:
                operand = insns[0].op_str
        except Exception:
            pass

        rows.append((address, disp, name, operand))
        i += size

    if args.markdown:
        print("| Address | Offset | Candidate method | Operand |")
        print("|---|---:|---|---|")
        for address, disp, name, operand in rows:
            print(f"| `0x{address:08x}` | `0x{disp:02x}` | {name} | `{operand}` |")
    else:
        for address, disp, name, operand in rows:
            print(f"0x{address:08x} +0x{disp:02x} {name:45s} {operand}")


if __name__ == "__main__":
    main()

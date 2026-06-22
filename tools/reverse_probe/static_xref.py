#!/usr/bin/env python3
import argparse
import bisect
import re
import struct
from collections import defaultdict
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, Cs


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "China2EX_fontfix8.exe"


def find_section(pe, name):
    wanted = name.encode("ascii")
    for section in pe.sections:
        if section.Name.rstrip(b"\0") == wanted:
            return section
    raise SystemExit(f"missing section {name}")


def section_bounds(pe, section):
    base = pe.OPTIONAL_HEADER.ImageBase
    start = base + section.VirtualAddress
    size = max(section.Misc_VirtualSize, section.SizeOfRawData)
    return start, start + size


def va_to_offset(pe, va):
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_c_string(data, offset):
    end = data.find(b"\0", offset)
    if end < 0:
        end = len(data)
    return data[offset:end]


def printable_strings(data, min_len=4):
    pattern = rb"[\x20-\x7e]{%d,}" % min_len
    for match in re.finditer(pattern, data):
        yield match.start(), match.group(0).decode("ascii", "replace")


def disassemble_text(pe, data):
    text = find_section(pe, ".text")
    base = pe.OPTIONAL_HEADER.ImageBase
    text_va = base + text.VirtualAddress
    text_data = data[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    return list(md.disasm(text_data, text_va))


def build_functions(insns, text_start, text_end, imports):
    starts = {text_start}
    call_targets = defaultdict(list)
    for ins in insns:
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            target = int(ins.op_str, 16)
            if text_start <= target < text_end:
                starts.add(target)
                call_targets[ins.address].append(target)
    # MSVC-like prologues are useful extra anchors in this binary.
    for idx, ins in enumerate(insns[:-2]):
        if ins.mnemonic == "push" and ins.op_str == "ebp":
            nxt = insns[idx + 1]
            if nxt.mnemonic == "mov" and nxt.op_str == "ebp, esp":
                starts.add(ins.address)

    starts = sorted(starts)
    funcs = {}
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else text_end
        funcs[start] = {"start": start, "end": end, "calls": set(), "imports": set(), "xrefs": set()}

    for ins in insns:
        idx = bisect.bisect_right(starts, ins.address) - 1
        if idx < 0:
            continue
        f = funcs[starts[idx]]
        if ins.mnemonic == "call":
            if ins.op_str.startswith("0x"):
                target = int(ins.op_str, 16)
                if text_start <= target < text_end:
                    f["calls"].add(target)
            else:
                for iat, name in imports.items():
                    if f"0x{iat:x}" in ins.op_str:
                        f["imports"].add(name)
        for iat, name in imports.items():
            if f"0x{iat:x}" in ins.op_str:
                f["imports"].add(name)
    return funcs, starts


def import_map(pe):
    out = {}
    if not hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        return out
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode("ascii", "replace")
        for imp in entry.imports:
            if imp.name:
                name = imp.name.decode("ascii", "replace")
            else:
                name = f"#{imp.ordinal}"
            out[imp.address] = f"{dll}!{name}"
    return out


def find_string_xrefs(pe, data, insns, strings, needle=None):
    text = find_section(pe, ".text")
    text_start, text_end = section_bounds(pe, text)
    by_va = {}
    needle_lc = needle.lower() if needle else None
    for offset, text_value in strings:
        if needle_lc and needle_lc not in text_value.lower():
            continue
        try:
            va = pe.OPTIONAL_HEADER.ImageBase + pe.get_rva_from_offset(offset)
        except Exception:
            continue
        by_va[va] = text_value

    refs = defaultdict(list)
    va_values = set(by_va)
    for ins in insns:
        operands = []
        try:
            operands = ins.operands
        except Exception:
            operands = []
        for op in operands:
            candidate = None
            if op.type == CS_OP_IMM:
                candidate = op.imm
            elif op.type == CS_OP_MEM and op.mem.disp:
                candidate = op.mem.disp
            if candidate in va_values:
                refs[by_va[candidate]].append(ins.address)
    return refs


def func_for(starts, addr):
    idx = bisect.bisect_right(starts, addr) - 1
    return starts[idx] if idx >= 0 else None


def main():
    parser = argparse.ArgumentParser(description="Build lightweight xref/function indexes for the China2 executable.")
    parser.add_argument("exe", nargs="?", default=str(DEFAULT_EXE))
    parser.add_argument("--strings", action="store_true", help="Print resource-like strings and xrefs.")
    parser.add_argument("--functions", action="store_true", help="Print likely functions touching useful imports or strings.")
    parser.add_argument("--xref", help="Print string xrefs containing this substring.")
    parser.add_argument("--disasm", help="Disassemble a function containing this VA, e.g. 0x478eb0.")
    parser.add_argument("--bytes", type=lambda x: int(x, 0), help="With --disasm, disassemble this many bytes from the given VA.")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    exe = Path(args.exe)
    data = exe.read_bytes()
    pe = pefile.PE(str(exe))
    text = find_section(pe, ".text")
    text_start, text_end = section_bounds(pe, text)
    imports = import_map(pe)
    insns = disassemble_text(pe, data)
    funcs, starts = build_functions(insns, text_start, text_end, imports)
    strings = None
    refs = None

    if args.disasm:
        va = int(args.disasm, 16)
        if args.bytes:
            start = va
            end = va + args.bytes
        else:
            start = func_for(starts, va)
            if start is None:
                raise SystemExit(f"no containing function for 0x{va:x}")
            end = funcs[start]["end"]
        for ins in insns:
            if start <= ins.address < end:
                print(f"{ins.address:08x}: {ins.mnemonic:7s} {ins.op_str}")
        return

    if args.xref:
        strings = list(printable_strings(data))
        refs = find_string_xrefs(pe, data, insns, strings, args.xref)
        needle = args.xref.lower()
        shown = 0
        for text_value in sorted(refs):
            if needle not in text_value.lower():
                continue
            for ref in refs[text_value]:
                f = func_for(starts, ref)
                print(f"0x{ref:08x} in 0x{f:08x}: {text_value}")
                shown += 1
                if shown >= args.limit:
                    return
        return

    if args.strings:
        strings = list(printable_strings(data))
        refs = find_string_xrefs(pe, data, insns, strings)
        shown = 0
        resource_rx = re.compile(r"(\\.EMG|\\.XMG|\\.TMG|\\.IMG|\\.IDI|\\.DAT|GRAPH|IMAGE|MUSIC|SAVE|Main|Menu|City|Battle|MAP|LDN)", re.I)
        for offset, text_value in strings:
            if not resource_rx.search(text_value):
                continue
            try:
                va = pe.OPTIONAL_HEADER.ImageBase + pe.get_rva_from_offset(offset)
            except Exception:
                va = 0
            ref_list = refs.get(text_value, [])
            ref_text = ", ".join(f"0x{x:08x}" for x in ref_list[:6])
            print(f"0x{va:08x}: {text_value}    refs: {ref_text}")
            shown += 1
            if shown >= args.limit:
                break

    if args.functions:
        interesting_imports = ("CreateFile", "ReadFile", "WriteFile", "GetTickCount", "DirectDraw", "wave", "mci", "LoadLibrary", "GetProcAddress")
        rows = []
        for start, f in funcs.items():
            score = len(f["calls"])
            score += 4 * sum(any(k in imp for k in interesting_imports) for imp in f["imports"])
            if score <= 0:
                continue
            rows.append((score, start, f))
        for score, start, f in sorted(rows, reverse=True)[:args.limit]:
            imps = ", ".join(sorted(f["imports"])[:8])
            calls = ", ".join(f"0x{x:08x}" for x in sorted(f["calls"])[:8])
            print(f"0x{start:08x}-0x{f['end']:08x} score={score} imports=[{imps}] calls=[{calls}]")


if __name__ == "__main__":
    main()

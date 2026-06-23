#!/usr/bin/env python3
import hashlib
import gzip
import json
import struct
from pathlib import Path

import map_model


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "remake-workbench" / "output"
OUT_FILE = OUT_DIR / "resource_inventory.json"
SUMMARY_FILE = OUT_DIR / "resource_inventory_summary.json"

RESOURCE_DIRS = [
    "Anim",
    "EDIT",
    "EMG",
    "Font",
    "GRAPH",
    "IMAGE",
    "MUSIC",
    "Save",
]

DAT_FILES = [
    "CONFIG.DAT",
    "C_TABLE.DAT",
    "D_TABLE.DAT",
    "F_TABLE.DAT",
    "KEYDEF.DAT",
    "SAVE.DAT",
    "SCORE.DAT",
]

INFERRED_TABLES = {
    "LandTile": {"stride": 0x100, "source": "Load_Dat / STRUCTURE_NOTES"},
    "CountryState": {"stride": 0xE68, "count": 22, "source": "Load_Dat"},
    "City": {"stride": "0x1b8+", "source": "Do_City / Load_Dat"},
    "ArmyTypeDef": {"stride": 0x400, "count": 91, "source": "Load_Dat"},
    "BuildingDef": {"stride": 0x200, "count": 65, "source": "Load_Dat"},
    "SpecialProjectDef": {"stride": 0x200, "count": 25, "source": "Load_Dat"},
    "ScienceDef": {"stride": 0x88, "count": 200, "source": "Load_Dat"},
    "CityResourceDef": {"stride": 0xD8, "count": 40, "source": "Load_Dat"},
    "CountryProfileDef": {"stride": 0x7C, "count": 100, "source": "Load_Dat"},
    "EmpireCountryDef": {"stride": 0x200, "count": 100, "source": "Load_Dat"},
    "GovernmentDef": {"stride": 0x74, "count": 8, "source": "Load_Dat"},
    "GroundDef": {"stride": 0x24, "count": 15, "source": "Load_Dat"},
    "BattleGridCell": {"stride": 0x30, "count": 24 * 24, "source": "Make_Battle_Map"},
    "MapNamedPoint": {"stride": 0x20, "counts": [1000, 4500], "source": "Load_Dat"},
}

def sha1(path):
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def pcx_tmg_info(path):
    raw = path.read_bytes()
    if len(raw) < 128 or raw[0] != 0x0A:
        return None
    xmin = read_u16(raw, 4)
    ymin = read_u16(raw, 6)
    xmax = read_u16(raw, 8)
    ymax = read_u16(raw, 10)
    return {
        "format": "pcx24_or_tmg",
        "width": xmax - xmin + 1,
        "height": ymax - ymin + 1,
        "bbox": [xmin, ymin, xmax, ymax],
        "bpp": raw[3],
        "planes": raw[65],
        "bytes_per_line": read_u16(raw, 66),
    }


def emg_summary(path):
    data = path.read_bytes()
    if len(data) < 2:
        return None
    group_count = read_u16(data, 0)
    if group_count > 10000:
        return None
    offset = 2
    groups = []
    flagged_frame_count = 0
    raw16_frame_count = 0
    try:
        for group_index in range(group_count):
            frame_count = read_u16(data, offset)
            group_offset = offset
            offset += 2
            frames = []
            for _ in range(frame_count):
                if offset + 6 > len(data):
                    raise ValueError("frame header overrun")
                x, y, width_or_flag = struct.unpack_from("<HHH", data, offset)
                frame_offset = offset
                if (width_or_flag & 0x8000) == 0:
                    payload_size = width_or_flag * 2
                    frame_format = "raw16"
                    raw16_frame_count += 1
                    width_value = width_or_flag
                    offset += 6 + payload_size
                else:
                    width_value = width_or_flag & 0x7FFF
                    payload_size = width_value * 3
                    frame_format = "flagged24"
                    flagged_frame_count += 1
                    offset += (width_value + 2) * 3
                if offset > len(data):
                    raise ValueError("frame payload overrun")
                frames.append({
                    "offset": frame_offset,
                    "x": x,
                    "y": y,
                    "width_value": width_value,
                    "payload_size": payload_size,
                    "format": frame_format,
                })
            groups.append({
                "index": group_index,
                "offset": group_offset,
                "frame_count": frame_count,
                "frames_sample": frames[:12],
            })
    except (struct.error, ValueError):
        return None
    fmt = "emg_raw16"
    if flagged_frame_count and raw16_frame_count:
        fmt = "emg_xmg_mixed"
    elif flagged_frame_count:
        fmt = "xmg_flagged24"
    return {
        "format": fmt,
        "group_count": group_count,
        "parsed_size": offset,
        "trailing_size": len(data) - offset,
        "raw16_frame_count": raw16_frame_count,
        "flagged24_frame_count": flagged_frame_count,
        "groups_sample": groups[:20],
    }


def gzip_info(path):
    data = path.read_bytes()
    if len(data) < 2 or data[:2] != b"\x1f\x8b":
        return None
    info = {
        "format": "gzip_stream",
        "gzip_magic": True,
    }
    try:
        decompressed = gzip.decompress(data)
        info["decompressed_size"] = len(decompressed)
        info["decompressed_sha1"] = hashlib.sha1(decompressed).hexdigest()
        info["decompressed_head_hex"] = decompressed[:64].hex()
        model = map_model.infer_map_model(path, decompressed)
        if model:
            info["map_model"] = model
    except OSError as exc:
        info["error"] = str(exc)
    return info


def file_info(path):
    rel = path.relative_to(ROOT).as_posix()
    info = {
        "path": rel,
        "name": path.name,
        "extension": path.suffix.lower(),
        "size": path.stat().st_size,
        "sha1": sha1(path),
    }
    ext = path.suffix.lower()
    if ext in [".pcx", ".tmg"]:
        parsed = pcx_tmg_info(path)
        if parsed:
            info["parsed"] = parsed
    elif ext in [".emg", ".xmg"]:
        parsed = emg_summary(path)
        if parsed:
            info["parsed"] = parsed
    elif ext == ".mgi":
        parsed = map_model.mgi_info(path)
        if parsed:
            info["parsed"] = parsed
    elif ext == ".map":
        parsed = gzip_info(path)
        if parsed:
            info["parsed"] = parsed
    return info


def scan_resource_dirs():
    resources = []
    by_extension = {}
    for name in RESOURCE_DIRS:
        directory = ROOT / name
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            info = file_info(path)
            resources.append(info)
            ext = info["extension"] or "<none>"
            stat = by_extension.setdefault(ext, {"count": 0, "bytes": 0})
            stat["count"] += 1
            stat["bytes"] += info["size"]
    return resources, by_extension


def scan_dat_files():
    files = []
    for name in DAT_FILES:
        path = ROOT / name
        if path.exists():
            files.append(file_info(path))
    return files


def main():
    resources, by_extension = scan_resource_dirs()
    parse_coverage = {}
    for ext in [".pcx", ".tmg", ".emg", ".xmg", ".mgi", ".map"]:
        files = [item for item in resources if item["extension"] == ext]
        parsed = [item for item in files if "parsed" in item]
        parse_coverage[ext] = {
            "files": len(files),
            "parsed": len(parsed),
            "unparsed": len(files) - len(parsed),
        }
    inventory = {
        "workspace": str(ROOT),
        "resource_dirs": RESOURCE_DIRS,
        "resource_count": len(resources),
        "resource_bytes": sum(item["size"] for item in resources),
        "by_extension": dict(sorted(by_extension.items())),
        "parse_coverage": parse_coverage,
        "resources": resources,
        "dat_files": scan_dat_files(),
        "inferred_tables": INFERRED_TABLES,
        "reverse_sources": [
            "reverse/ghidra_export/STRUCTURE_NOTES.md",
            "reverse/ghidra_export/UNCERTAINTIES.md",
            "reverse/ghidra_export/game/load_dat.c",
            "reverse/ghidra_export/game/do_city.c",
            "reverse/ghidra_export/game/city_resource_change.c",
            "reverse/ghidra_export/game/city_building.c",
            "reverse/ghidra_export/game/do_battle_army_and_die.c",
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "workspace": inventory["workspace"],
        "resource_count": inventory["resource_count"],
        "resource_bytes": inventory["resource_bytes"],
        "by_extension": inventory["by_extension"],
        "parse_coverage": inventory["parse_coverage"],
        "map_models": [
            {
                "path": item["path"],
                **item["parsed"]["map_model"],
            }
            for item in resources
            if item.get("parsed", {}).get("map_model")
        ],
        "inferred_tables": inventory["inferred_tables"],
        "reverse_sources": inventory["reverse_sources"],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_FILE}")
    print(f"wrote {SUMMARY_FILE}")
    print(f"resources: {inventory['resource_count']} files, {inventory['resource_bytes']} bytes")
    for ext, stat in inventory["by_extension"].items():
        print(f"{ext}: {stat['count']} files, {stat['bytes']} bytes")
    print("parse coverage:")
    for ext, stat in parse_coverage.items():
        print(f"{ext}: {stat['parsed']} / {stat['files']} parsed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import hashlib
import gzip
import json
import struct
from pathlib import Path


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

STATIC_MAP_PREFIX_BLOCKS = [
    ("science_defs", 0x6A40),
    ("army_type_defs", 0x16C00),
    ("building_defs", 0xC000),
    ("country_profile_defs", 0x3070),
    ("government_defs", 0x3A0),
    ("ground_defs", 0x21C),
    ("city_resource_defs", 0x21C0),
    ("flag_img_bank", 100 * 0x100),
]

MAP_SIZE_MODES = {
    0: {"width": 0x138, "height": 0x192, "label": "large_312x402"},
    1: {"width": 0x9C, "height": 0xC9, "label": "big_156x201"},
    2: {"width": 0x4E, "height": 100, "label": "mid_78x100"},
    3: {"width": 0x27, "height": 0x32, "label": "small_39x50"},
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
    if group_count > 2000:
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


def read_c_string(data, offset, size):
    chunk = data[offset:offset + size]
    return chunk.split(b"\x00", 1)[0].decode("gbk", errors="replace")


def read_i32(data, offset):
    return struct.unpack_from("<i", data, offset)[0]


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def mgi_info(path):
    data = path.read_bytes()
    if len(data) < 8:
        return None
    major = read_u32(data, 0)
    minor = read_u32(data, 4)
    version_score = major * 100 + minor
    record_offset = 8
    if len(data) < record_offset + 0x168:
        return None
    return {
        "format": "mgi_scenario_info",
        "version_major": major,
        "version_minor": minor,
        "version_score": version_score,
        "record_offset": record_offset,
        "record_size_available": len(data) - record_offset,
        "file_name": read_c_string(data, record_offset + 0x00, 17),
        "map_name": read_c_string(data, record_offset + 0x11, 23),
        "edit_status_mode": read_i32(data, record_offset + 0x28),
        "gameplay_mode": read_i32(data, record_offset + 0x2C),
        "difficulty_level": read_i32(data, record_offset + 0x30),
        "subtitle_or_author": read_c_string(data, record_offset + 0x34, 17),
        "description_short": read_c_string(data, record_offset + 0x45, 19),
        "player_country_id": read_i32(data, record_offset + 0x58),
        "current_year": read_i32(data, record_offset + 0x5C),
        "country_count": read_i32(data, record_offset + 0x60),
        "country_limit": read_i32(data, record_offset + 0x64),
        "barbarian_setting": read_i32(data, record_offset + 0xD4),
        "city_resource_system_enabled": read_i32(data, record_offset + 0xE8),
        "corruption_deduction_mode": read_i32(data, record_offset + 0xEC),
        "scenario_rule_values": [
            read_i32(data, record_offset + 0xF0),
            read_i32(data, record_offset + 0xF4),
            read_i32(data, record_offset + 0xF8),
            read_i32(data, record_offset + 0xFC),
        ],
        "auto_city_processing_countdown": read_i32(data, record_offset + 0x100),
        "map_size_mode": read_i32(data, record_offset + 0x104),
        "science_table_choice": read_i32(data, record_offset + 0x108),
        "description_long": read_c_string(data, record_offset + 0x10C, 64),
        "horizontal_wrap_setting": read_i32(data, record_offset + 0x14C),
        "place_name_setting": read_i32(data, record_offset + 0x150),
        "scenario_value_154": read_i32(data, record_offset + 0x154),
        "scripted_start_or_generated_flag": read_i32(data, record_offset + 0x158),
        "scenario_value_15c": read_i32(data, record_offset + 0x15C),
        "scenario_value_160": read_i32(data, record_offset + 0x160),
        "movement_base": read_i32(data, record_offset + 0x164),
        "score_history_scenario_flag": read_i32(data, record_offset + 0x168),
    }


def map_model_info(path, decompressed):
    mgi_path = path.with_suffix(".MGI")
    if not mgi_path.exists():
        return None
    mgi = mgi_info(mgi_path)
    if not mgi:
        return None
    mode = mgi["map_size_mode"]
    size_mode = MAP_SIZE_MODES.get(mode)
    if not size_mode:
        return {"error": f"unknown map_size_mode {mode}"}

    prefix_size = sum(size for _, size in STATIC_MAP_PREFIX_BLOCKS)
    width = size_mode["width"]
    height = size_mode["height"]
    tile_count = width * height
    land_offset = prefix_size
    land_bytes = tile_count * 0x100
    after_land_offset = land_offset + land_bytes
    if len(decompressed) < after_land_offset + 12:
        return {
            "error": "decompressed stream shorter than inferred land block",
            "map_size_mode": mode,
            "width": width,
            "height": height,
            "land_offset": land_offset,
            "land_bytes": land_bytes,
        }

    terrain_histogram = {}
    battle_feature_count = 0
    city_resource_count = 0
    owned_tile_count = 0
    for index in range(tile_count):
        offset = land_offset + index * 0x100
        terrain = struct.unpack_from("<b", decompressed, offset)[0]
        terrain_histogram[str(terrain)] = terrain_histogram.get(str(terrain), 0) + 1
        if struct.unpack_from("<b", decompressed, offset + 0x16)[0] >= 0:
            battle_feature_count += 1
        if struct.unpack_from("<b", decompressed, offset + 0x17)[0] >= 0:
            city_resource_count += 1
        if struct.unpack_from("<b", decompressed, offset + 0x25)[0] >= 0:
            owned_tile_count += 1

    block_offsets = []
    offset = 0
    for name, size in STATIC_MAP_PREFIX_BLOCKS:
        block_offsets.append({"name": name, "offset": offset, "size": size})
        offset += size

    return {
        "map_size_mode": mode,
        "size_label": size_mode["label"],
        "width": width,
        "height": height,
        "tile_count": tile_count,
        "static_prefix_size": prefix_size,
        "static_prefix_blocks": block_offsets,
        "land_offset": land_offset,
        "land_bytes": land_bytes,
        "post_land_offset": after_land_offset,
        "saved_view_x": read_i32(decompressed, after_land_offset),
        "saved_view_y": read_i32(decompressed, after_land_offset + 4),
        "land_record_capacity": read_i32(decompressed, after_land_offset + 8),
        "tail_offset": after_land_offset + 12,
        "tail_size": len(decompressed) - (after_land_offset + 12),
        "terrain_kind_histogram": terrain_histogram,
        "battle_feature_tile_count": battle_feature_count,
        "city_resource_tile_count": city_resource_count,
        "owned_tile_count": owned_tile_count,
        "scenario": {
            "version_major": mgi["version_major"],
            "version_minor": mgi["version_minor"],
            "current_year": mgi["current_year"],
            "country_count": mgi["country_count"],
            "country_limit": mgi["country_limit"],
            "horizontal_wrap_setting": mgi["horizontal_wrap_setting"],
        },
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
        map_model = map_model_info(path, decompressed)
        if map_model:
            info["map_model"] = map_model
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
        parsed = mgi_info(path)
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

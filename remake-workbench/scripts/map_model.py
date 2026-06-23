#!/usr/bin/env python3
import gzip
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

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


def read_i8(data, offset):
    return struct.unpack_from("<b", data, offset)[0]


def read_i16(data, offset):
    return struct.unpack_from("<h", data, offset)[0]


def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def read_i32(data, offset):
    return struct.unpack_from("<i", data, offset)[0]


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def read_c_string(data, offset, size):
    chunk = data[offset:offset + size]
    return chunk.split(b"\x00", 1)[0].decode("gbk", errors="replace")


def resolve_workspace_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return ROOT / path


def mgi_info(path):
    data = resolve_workspace_path(path).read_bytes()
    if len(data) < 8:
        return None
    major = read_u32(data, 0)
    minor = read_u32(data, 4)
    record_offset = 8
    if len(data) < record_offset + 0x16C:
        return None
    return {
        "format": "mgi_scenario_info",
        "version_major": major,
        "version_minor": minor,
        "version_score": major * 100 + minor,
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


def infer_map_model(map_path, decompressed):
    map_path = resolve_workspace_path(map_path)
    mgi_path = map_path.with_suffix(".MGI")
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
        terrain = read_i8(decompressed, offset)
        terrain_histogram[str(terrain)] = terrain_histogram.get(str(terrain), 0) + 1
        if read_i8(decompressed, offset + 0x16) >= 0:
            battle_feature_count += 1
        if read_i8(decompressed, offset + 0x17) >= 0:
            city_resource_count += 1
        if read_i8(decompressed, offset + 0x25) >= 0:
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


def load_map(map_path):
    map_path = resolve_workspace_path(map_path)
    decompressed = gzip.decompress(map_path.read_bytes())
    model = infer_map_model(map_path, decompressed)
    if not model or "error" in model:
        raise RuntimeError(f"could not infer map model for {map_path}: {model}")
    return decompressed, model


def tile_offset(model, x, y, wrap=None):
    width = model["width"]
    height = model["height"]
    if wrap is None:
        wrap = model["scenario"]["horizontal_wrap_setting"] == 1
    if wrap:
        x %= width
    if x < 0 or width <= x or y < 0 or height <= y:
        raise IndexError(f"tile coordinate out of range: {x},{y} for {width}x{height}")
    return model["land_offset"] + (x + y * width) * 0x100


def tile_index(model, x, y, wrap=None):
    offset = tile_offset(model, x, y, wrap=wrap)
    return (offset - model["land_offset"]) // 0x100


def tile_summary(data, model, x, y):
    offset = tile_offset(model, x, y)
    normalized_index = (offset - model["land_offset"]) // 0x100
    normalized_x = normalized_index % model["width"]
    normalized_y = normalized_index // model["width"]
    return {
        "x": normalized_x,
        "y": normalized_y,
        "requested_x": x,
        "requested_y": y,
        "index": normalized_index,
        "offset": offset,
        "terrain_kind": read_i8(data, offset + 0x00),
        "alternate_battle_terrain": read_i8(data, offset + 0x02),
        "terrain_variant": read_i8(data, offset + 0x03),
        "terrain_sprite_id": read_u16(data, offset + 0x04),
        "special_terrain_sprite_id": read_u16(data, offset + 0x06),
        "terrain_detail_mode": read_i8(data, offset + 0x08),
        "terrain_detail_sprite_ids": [read_i8(data, offset + 0x09 + index) for index in range(6)],
        "terrain_layer_or_special_flag": read_i8(data, offset + 0x0F),
        "road_connection_tile_id": read_i8(data, offset + 0x13),
        "road_overlay_kind": read_i8(data, offset + 0x14),
        "bridge_variant_id": read_i8(data, offset + 0x15),
        "battle_feature_id": read_i8(data, offset + 0x16),
        "city_resource_id": read_i8(data, offset + 0x17),
        "long_wall_or_battle_bonus_mode": read_i8(data, offset + 0x24),
        "owner_country_id": read_i8(data, offset + 0x25),
        "secondary_owner_country_id": read_i8(data, offset + 0x27),
        "primary_army_count": read_i32(data, offset + 0x50),
        "secondary_occupant_count": read_i8(data, offset + 0x7C),
        "linked_city_or_object_ptr": read_u32(data, offset + 0x88),
        "linked_resource_city_ptr": read_u32(data, offset + 0x8C),
        "primary_named_point_index": read_i16(data, offset + 0xAE),
        "secondary_named_point_index": read_i16(data, offset + 0xB0),
        "city_resource_stockpile": read_i32(data, offset + 0xF8),
    }


def default_tiles(model):
    width = model["width"]
    height = model["height"]
    return [
        (0, 0),
        (width // 2, height // 2),
        (width - 1, height - 1),
    ]

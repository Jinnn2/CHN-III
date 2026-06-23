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

COUNTRY_STATE_RECORD_SIZE = 0xE68
COUNTRY_STATE_COUNT = 22
EMPIRE_COUNTRY_DEFS_SIZE = 0xC800
COUNTRY_STATES_SIZE = COUNTRY_STATE_RECORD_SIZE * COUNTRY_STATE_COUNT
SAVE_SECTION_TAG_SIZE = 5
LIVE_RECORD_COUNT_SIZE = 4
CITY_RECORD_SIZE = 0x200
CITY_MAP_BLOCK_SIZE = 0x12000

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
        "post_view_state_offset": after_land_offset + 12,
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


def country_states_offset(model):
    return model["post_view_state_offset"] + EMPIRE_COUNTRY_DEFS_SIZE


def post_country_states_offset(model):
    return country_states_offset(model) + COUNTRY_STATES_SIZE


def country_state_summary(data, model, country_id):
    offset = country_states_offset(model) + country_id * COUNTRY_STATE_RECORD_SIZE
    if offset + COUNTRY_STATE_RECORD_SIZE > len(data):
        raise IndexError(f"country state {country_id} outside MAP data")
    return {
        "country_id": country_id,
        "offset": offset,
        "is_active": read_i8(data, offset),
        "profile_id": read_i8(data, offset + 0x03),
        "load_dat_city_record_count": read_u16(data, offset + 0x1AA),
        "load_dat_army_record_count": read_u16(data, offset + 0x7C),
    }


def save_tail_city_section_offset(data, model):
    """Return the first City_0x200 record offset, or None for template maps.

    Load_Dat reads, after LandTile and view state:
    empire country defs, 22 CountryState_0xe68 records, three dwords, a 5-byte
    city section tag, then a 4-byte live city count. City records follow.
    """
    post_country = post_country_states_offset(model)
    city_start = post_country + 12 + SAVE_SECTION_TAG_SIZE + LIVE_RECORD_COUNT_SIZE
    if city_start + CITY_RECORD_SIZE > len(data):
        return None
    return city_start


def parse_save_tail_cities(data, model, include_city_map=True):
    city_start = save_tail_city_section_offset(data, model)
    if city_start is None:
        return {
            "status": "no_live_save_tail",
            "city_record_count": 0,
            "cities": [],
        }

    countries = [country_state_summary(data, model, index) for index in range(COUNTRY_STATE_COUNT)]
    expected_count = sum(
        country["load_dat_city_record_count"]
        for country in countries
        if country["is_active"] > 0
    )
    stored_count_offset = post_country_states_offset(model) + 12 + SAVE_SECTION_TAG_SIZE
    stored_count = read_i32(data, stored_count_offset)
    stride = CITY_RECORD_SIZE + (CITY_MAP_BLOCK_SIZE if include_city_map else 0)
    cities = []
    offset = city_start
    for country in countries:
        if country["is_active"] <= 0:
            continue
        count = country["load_dat_city_record_count"]
        for local_index in range(count):
            if offset + CITY_RECORD_SIZE > len(data):
                return {
                    "status": "truncated_city_records",
                    "city_record_count": len(cities),
                    "expected_city_record_count": expected_count,
                    "stored_city_record_count": stored_count,
                    "cities": cities,
                }
            owner = read_i8(data, offset + 0x01)
            x = read_u16(data, offset + 0x16)
            y = read_u16(data, offset + 0x18)
            name = read_c_string(data, offset + 0x03, 0x13)
            valid = (
                0 <= owner < COUNTRY_STATE_COUNT
                and 0 <= x < model["width"]
                and 0 <= y < model["height"]
            )
            cities.append({
                "index": len(cities),
                "country_id_from_loop": country["country_id"],
                "local_index": local_index,
                "offset": offset,
                "owner_country_id": owner,
                "name": name,
                "x": x,
                "y": y,
                "city_sprite_level": read_i8(data, offset + 0x21),
                "city_sprite_level_from_population": city_sprite_level_from_population(read_i32(data, offset + 0x24)),
                "city_status_flag": read_i8(data, offset + 0x2E),
                "city_view_mode": read_i32(data, offset + 0x28),
                "population_or_output": read_i32(data, offset + 0x24),
                "development_stat": read_i32(data, offset + 0x4C),
                "safety_stat": read_i32(data, offset + 0x50),
                "resource_stat": read_i32(data, offset + 0x54),
                "production_mode": read_i8(data, offset + 0x5C),
                "valid_position": valid,
                "evidence_level": "strong_inference",
            })
            offset += stride

    status = "ok"
    if stored_count != expected_count:
        status = "count_mismatch"
    if any(not city["valid_position"] for city in cities):
        status = "invalid_city_position"
    return {
        "status": status,
        "section_offset": city_start,
        "stored_city_record_count": stored_count,
        "expected_city_record_count": expected_count,
        "city_record_count": len(cities),
        "city_record_stride": stride,
        "include_city_map": include_city_map,
        "countries": countries,
        "cities": cities,
    }


def city_sprite_level_from_population(population):
    if population < 50000:
        return 0
    if population < 200000:
        return 1
    if population < 400000:
        return 2
    if population < 1200000:
        return 3
    if population < 1800000:
        return 4
    if population < 2600000:
        return 5
    if population < 5000000:
        return 6
    return 7


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


HEX_NEIGHBOR_DELTAS = {
    0: [(-1, 1), (-1, -1), (0, -1), (0, 1)],
    1: [(0, 1), (0, -1), (1, -1), (1, 1)],
}

ROAD_HEIGHT_MODE_BY_DETAIL = [0, 1, 1, 1, 2, 2]


def neighbor_tile_summary(data, model, x, y, direction_index):
    dx, dy = HEX_NEIGHBOR_DELTAS[y & 1][direction_index]
    try:
        return tile_summary(data, model, x + dx, y + dy)
    except IndexError:
        return None


def decode_road_connection_id(data, model, x, y):
    tile = tile_summary(data, model, x, y)
    if tile["road_connection_tile_id"] < 0:
        return -1

    current_height = ROAD_HEIGHT_MODE_BY_DETAIL[tile["terrain_detail_mode"]]
    result = 0
    directions = [
        (0, 9, 9),
        (1, 0x36, 0x1B),
        (2, 2, 1),
        (3, 6, 3),
    ]
    for direction_index, high_delta, low_delta in directions:
        neighbor = neighbor_tile_summary(data, model, x, y, direction_index)
        if not neighbor:
            continue
        connects = (
            neighbor["road_connection_tile_id"] >= 0
            or neighbor["bridge_variant_id"] >= 0
        )
        passable = neighbor["terrain_kind"] < 11 or tile["terrain_kind"] < 11
        if not connects or not passable:
            continue
        neighbor_height = ROAD_HEIGHT_MODE_BY_DETAIL[neighbor["terrain_detail_mode"]]
        if current_height < neighbor_height:
            result += high_delta
        else:
            result += low_delta
    return result

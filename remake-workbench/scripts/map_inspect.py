#!/usr/bin/env python3
import argparse
import gzip
import json
import struct
import sys
from pathlib import Path

import inventory


ROOT = Path(__file__).resolve().parents[2]


def read_i8(data, offset):
    return struct.unpack_from("<b", data, offset)[0]


def read_i16(data, offset):
    return struct.unpack_from("<h", data, offset)[0]


def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def read_i32(data, offset):
    return struct.unpack_from("<i", data, offset)[0]


def parse_tile_coord(raw):
    try:
        x_raw, y_raw = raw.split(",", 1)
        return int(x_raw, 0), int(y_raw, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("tile must be formatted as x,y") from exc


def load_map(map_path):
    data = gzip.decompress(map_path.read_bytes())
    model = inventory.map_model_info(map_path, data)
    if not model or "error" in model:
        raise RuntimeError(f"could not infer map model for {map_path}: {model}")
    return data, model


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


def tile_summary(data, model, x, y):
    offset = tile_offset(model, x, y)
    return {
        "x": x,
        "y": y,
        "index": x + y * model["width"],
        "offset": offset,
        "terrain_kind": read_i8(data, offset + 0x00),
        "alternate_battle_terrain": read_i8(data, offset + 0x02),
        "terrain_variant": read_i8(data, offset + 0x03),
        "terrain_sprite_id": read_u16(data, offset + 0x04),
        "special_terrain_sprite_id": read_u16(data, offset + 0x06),
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect a decompressed MAP/MGI model boundary.")
    parser.add_argument("map", nargs="?", default="Save/WORLD_FLAT.MAP", help="Path to a .MAP file")
    parser.add_argument("--tile", action="append", type=parse_tile_coord, help="Tile coordinate as x,y")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    map_path = (ROOT / args.map).resolve()
    data, model = load_map(map_path)
    coords = args.tile or default_tiles(model)
    result = {
        "path": map_path.relative_to(ROOT).as_posix(),
        "model": {
            key: model[key]
            for key in [
                "map_size_mode",
                "size_label",
                "width",
                "height",
                "tile_count",
                "land_offset",
                "land_bytes",
                "tail_offset",
                "tail_size",
            ]
        },
        "scenario": model["scenario"],
        "tiles": [tile_summary(data, model, x, y) for x, y in coords],
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"{result['path']}: {model['size_label']} {model['width']}x{model['height']}")
    print(
        "land_offset=0x%x land_bytes=%d tail_size=%d"
        % (model["land_offset"], model["land_bytes"], model["tail_size"])
    )
    print(
        "scenario: year=%s countries=%s/%s wrap=%s"
        % (
            model["scenario"]["current_year"],
            model["scenario"]["country_count"],
            model["scenario"]["country_limit"],
            model["scenario"]["horizontal_wrap_setting"],
        )
    )
    for tile in result["tiles"]:
        print(
            "tile {x},{y} terrain={terrain_kind} sprite={terrain_sprite_id} "
            "battle_feature={battle_feature_id} city_resource={city_resource_id} "
            "owner={owner_country_id} stockpile={city_resource_stockpile}".format(**tile)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

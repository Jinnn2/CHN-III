#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import map_model


ROOT = Path(__file__).resolve().parents[2]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_tile_coord(raw):
    try:
        x_raw, y_raw = raw.split(",", 1)
        return int(x_raw, 0), int(y_raw, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("tile must be formatted as x,y") from exc




def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect a decompressed MAP/MGI model boundary.")
    parser.add_argument("map", nargs="?", default="Save/WORLD_FLAT.MAP", help="Path to a .MAP file")
    parser.add_argument("--tile", action="append", type=parse_tile_coord, help="Tile coordinate as x,y")
    parser.add_argument("--cities", action="store_true", help="Show parsed live save-tail city records")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    map_path = (ROOT / args.map).resolve()
    data, model = map_model.load_map(map_path)
    coords = args.tile or map_model.default_tiles(model)
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
        "tiles": [map_model.tile_summary(data, model, x, y) for x, y in coords],
    }
    if args.cities:
        result["cities"] = map_model.parse_save_tail_cities(data, model)
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
            "detail_mode={terrain_detail_mode} details={terrain_detail_sprite_ids} "
            "road={road_connection_tile_id}/{road_overlay_kind} bridge={bridge_variant_id} "
            "wall={long_wall_or_battle_bonus_mode} city_ptr=0x{linked_city_or_object_ptr:08x} "
            "battle_feature={battle_feature_id} city_resource={city_resource_id} "
            "owner={owner_country_id} stockpile={city_resource_stockpile}".format(**tile)
        )
    if args.cities:
        cities = result["cities"]
        print(
            "cities: status=%s count=%s stored=%s stride=0x%x"
            % (
                cities["status"],
                cities["city_record_count"],
                cities.get("stored_city_record_count", 0),
                cities.get("city_record_stride", 0),
            )
        )
        for city in cities["cities"][:20]:
            print(
                "  city #{index} owner={owner_country_id} tile={x},{y} name={name}".format(**city)
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

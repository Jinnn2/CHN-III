#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import map_model
import map_resources


ROOT = Path(__file__).resolve().parents[2]


def inspect(path):
    data, model = map_model.load_map(path)
    counts = {
        "road": {},
        "road_kind": {},
        "bridge": {},
        "long_wall": {},
    }
    samples = []
    for y in range(model["height"]):
        for x in range(model["width"]):
            tile = map_model.tile_summary(data, model, x, y)
            values = {
                "road": tile["road_connection_tile_id"],
                "road_kind": tile["road_overlay_kind"],
                "bridge": tile["bridge_variant_id"],
                "long_wall": tile["long_wall_or_battle_bonus_mode"],
            }
            for key, value in values.items():
                counts[key][str(value)] = counts[key].get(str(value), 0) + 1
            if (
                values["road"] >= 0
                or values["bridge"] >= 0
                or values["long_wall"] >= 0
            ):
                samples.append({
                    "x": x,
                    "y": y,
                    **values,
                    "decoded_road": map_model.decode_road_connection_id(data, model, x, y),
                })
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "width": model["width"],
        "height": model["height"],
        "decode_road_status": "confirmed_original_connection_field",
        "visual_mapping_status": "confirmed_original_world_map_draw_path",
        "world_map_draw_path": "reverse/ghidra_export/all_functions/0x004a3ce0_FUN_004a3ce0.c uses MAKE.EMG/DAT_0075856c with LandTile+0x14 * 0x51 + LandTile+0x13",
        "road_emg_known_use": "reverse/ghidra_export/extra/put_city_view.c draws city-view roads from DAT_00758590",
        "counts": counts,
        "positive_samples": samples,
        "manifest_layers": [
            layer
            for layer in map_resources.build_manifest()["layers"]
            if layer["canonical_layer"] == "roads"
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect a road-positive MAP sample.")
    parser.add_argument("map", nargs="?", default="Save/save.MAP")
    parser.add_argument("--out")
    args = parser.parse_args()
    path = Path(args.map)
    if not path.is_absolute():
        path = ROOT / path
    result = inspect(path)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

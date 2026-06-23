#!/usr/bin/env python3
import argparse
from pathlib import Path

import emg_sprites
import map_resources
import png_writer


def frame_metadata(bank):
    frames = []
    for sprite in bank["groups"]:
        width, height = emg_sprites.sprite_dimensions(sprite)
        frames.append({
            "source_group": sprite["index"],
            "source_offset": sprite["offset"],
            "segment_count": sprite["segment_count"],
            "pixel_count": sprite["pixel_count"],
            "bbox": sprite["bbox"],
            "width": width,
            "height": height,
        })
    return frames


def write_preview_atlas(path, bank, color_mode):
    frames = frame_metadata(bank)
    cell_w = max(max(frame["width"] for frame in frames), 1) + 2
    cell_h = max(max(frame["height"] for frame in frames), 1) + 2
    columns = 32
    rows = (len(frames) + columns - 1) // columns
    width = columns * cell_w
    height = rows * cell_h
    pixels = bytearray([0, 0, 0] * width * height)
    placements = []
    for index, sprite in enumerate(bank["groups"]):
        col = index % columns
        row = index // columns
        x = col * cell_w + 1 - sprite["bbox"][0]
        y = row * cell_h + 1 - sprite["bbox"][1]
        emg_sprites.draw_sprite(pixels, width, height, sprite, x, y, color_mode=color_mode)
        placements.append({
            "source_group": index,
            "atlas_x": col * cell_w + 1,
            "atlas_y": row * cell_h + 1,
            "width": frames[index]["width"],
            "height": frames[index]["height"],
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    png_writer.write_png_rgb(path, width, height, pixels)
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "cell_width": cell_w,
        "cell_height": cell_h,
        "columns": columns,
        "placements": placements,
    }


def main():
    parser = argparse.ArgumentParser(description="Export modern map resource manifests and atlas metadata.")
    parser.add_argument("--color-mode", choices=["565", "555"], default="565")
    parser.add_argument("--skip-atlas", action="store_true", help="Only write JSON manifests/metadata")
    args = parser.parse_args()

    manifest = map_resources.build_manifest()
    map_resources.write_json(map_resources.MANIFEST_DIR / "map_layers.json", manifest)
    map_resources.write_json(map_resources.MANIFEST_DIR / "source_banks.json", manifest["banks"])
    map_resources.write_json(map_resources.METADATA_DIR / "layer_draw_rules.json", manifest["layers"])
    (map_resources.OUT_ROOT / "diagnostics").mkdir(parents=True, exist_ok=True)

    atlas_manifest = {"atlases": []}
    for bank_def in manifest["banks"]:
        bank = emg_sprites.parse_emg(bank_def["source_path"])
        frames = frame_metadata(bank)
        map_resources.write_json(
            map_resources.METADATA_DIR / f"{bank_def['id']}.frames.json",
            {
                "bank": bank_def["id"],
                "source_path": bank_def["source_path"],
                "group_count": bank["group_count"],
                "frames": frames,
            },
        )
        if not args.skip_atlas:
            atlas_path = map_resources.ATLAS_DIR / f"{bank_def['id']}_preview_atlas.png"
            atlas = write_preview_atlas(atlas_path, bank, args.color_mode)
            atlas["bank"] = bank_def["id"]
            atlas_manifest["atlases"].append(atlas)
    if not args.skip_atlas:
        map_resources.write_json(map_resources.METADATA_DIR / "preview_atlases.json", atlas_manifest)

    print(f"wrote {map_resources.MANIFEST_DIR / 'map_layers.json'}")
    print(f"banks={len(manifest['banks'])} layers={len(manifest['layers'])}")


if __name__ == "__main__":
    main()

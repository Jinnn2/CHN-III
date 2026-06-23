#!/usr/bin/env python3
import argparse
from pathlib import Path

import emg_sprites
import map_resources
import map_model
import png_writer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "remake-workbench" / "output" / "previews"
NEW_GROUND_EMG = ROOT / "EMG" / "NEW_GROUND.EMG"
MAKE_EMG = ROOT / "EMG" / "MAKE.EMG"
ROAD_EMG = ROOT / "EMG" / "ROAD.EMG"
CITY_EMG = ROOT / "EMG" / "CITY.EMG"
RESOURCE_EMG = ROOT / "EMG" / "RESOURCE.EMG"
TERRAIN_DETAIL_BASE = map_resources.TERRAIN_DETAIL_BASE
TERRAIN_DETAIL_ALT_BASE = map_resources.TERRAIN_DETAIL_ALT_BASE
GROUND_RESOURCE_BASE = map_resources.GROUND_RESOURCE_BASE
ROAD_HEIGHT_DRAW_Y = [-12, 0, 12, 24, 36, 90, 90, 30, 60, 15]
ROAD_HEIGHT_MODE_BY_DETAIL = map_model.ROAD_HEIGHT_MODE_BY_DETAIL

TERRAIN_COLORS = {
    -1: (32, 32, 36),
    0: (88, 150, 74),
    1: (112, 174, 84),
    2: (170, 154, 98),
    3: (92, 132, 86),
    4: (128, 128, 104),
    5: (184, 176, 120),
    6: (44, 96, 168),
    7: (36, 82, 150),
    8: (40, 70, 126),
    9: (210, 202, 148),
    10: (168, 184, 140),
    11: (136, 116, 88),
    12: (160, 150, 132),
    13: (110, 106, 112),
    14: (198, 202, 198),
}

OWNER_COLORS = [
    (214, 67, 56),
    (70, 126, 214),
    (64, 164, 92),
    (219, 156, 45),
    (142, 91, 204),
    (46, 166, 172),
    (220, 92, 146),
    (120, 146, 54),
    (230, 110, 62),
    (100, 110, 210),
    (70, 150, 128),
    (184, 72, 86),
    (132, 112, 72),
    (84, 132, 184),
    (164, 84, 156),
    (96, 156, 70),
    (210, 190, 76),
    (72, 164, 204),
    (172, 96, 64),
    (190, 74, 178),
    (92, 92, 92),
    (150, 150, 150),
]


def parse_map_path(raw):
    path = Path(raw)
    if path.is_absolute():
        return path
    return ROOT / path


def blend(a, b, amount):
    return tuple(int(round(a[i] * (1.0 - amount) + b[i] * amount)) for i in range(3))


def tile_color(data, model, x, y, overlay):
    offset = map_model.tile_offset(model, x, y)
    terrain = map_model.read_i8(data, offset)
    color = TERRAIN_COLORS.get(terrain, (206, 80, 80))
    battle_feature = map_model.read_i8(data, offset + 0x16)
    city_resource = map_model.read_i8(data, offset + 0x17)
    owner = map_model.read_i8(data, offset + 0x25)

    if overlay in ("resources", "all"):
        if battle_feature >= 0:
            color = blend(color, (245, 202, 76), 0.55)
        if city_resource >= 0:
            color = blend(color, (84, 220, 122), 0.65)
    if overlay in ("owner", "all") and owner >= 0:
        color = blend(color, OWNER_COLORS[owner % len(OWNER_COLORS)], 0.55)
    return color


def render_preview(data, model, scale, overlay):
    width = model["width"]
    height = model["height"]
    out_width = width * scale
    out_height = height * scale
    pixels = bytearray(out_width * out_height * 3)
    for y in range(height):
        row_colors = [tile_color(data, model, x, y, overlay) for x in range(width)]
        for sy in range(scale):
            out_y = y * scale + sy
            row_start = out_y * out_width * 3
            for x, color in enumerate(row_colors):
                for sx in range(scale):
                    pos = row_start + (x * scale + sx) * 3
                    pixels[pos:pos + 3] = bytes(color)
    return out_width, out_height, pixels


def clamp_viewport(model, viewport):
    if viewport is None:
        if model["tile_count"] <= 10000:
            return 0, 0, model["width"], model["height"]
        width = min(96, model["width"])
        height = min(72, model["height"])
        return (model["width"] - width) // 2, (model["height"] - height) // 2, width, height
    x, y, width, height = viewport
    if width < 1 or height < 1:
        raise ValueError("viewport width and height must be positive")
    x = max(0, min(x, model["width"] - 1))
    y = max(0, min(y, model["height"] - 1))
    width = min(width, model["width"] - x)
    height = min(height, model["height"] - y)
    return x, y, width, height


def parse_viewport(raw):
    try:
        values = [int(part, 0) for part in raw.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("viewport must be x,y,width,height") from exc
    if len(values) != 4:
        raise argparse.ArgumentTypeError("viewport must be x,y,width,height")
    return tuple(values)


def terrain_sprite_id(data, model, x, y):
    tile = map_model.tile_summary(data, model, x, y)
    if tile["terrain_kind"] >= 11:
        sprite_id = tile["special_terrain_sprite_id"]
        if sprite_id >= 0:
            return sprite_id
    return tile["terrain_sprite_id"]


def terrain_detail_sprite_ids(data, model, x, y):
    tile = map_model.tile_summary(data, model, x, y)
    if tile["terrain_detail_mode"] <= 0 or tile["terrain_sprite_id"] >= 0x717:
        return []

    detail_ids = [value for value in tile["terrain_detail_sprite_ids"] if value >= 0]
    if not detail_ids:
        return []

    mode = tile["terrain_detail_mode"]
    if mode in (1, 2):
        return [(TERRAIN_DETAIL_BASE + value, 0) for value in detail_ids]
    if mode in (4, 5):
        return [(TERRAIN_DETAIL_BASE + detail_ids[0], 2)]
    return [(TERRAIN_DETAIL_ALT_BASE + detail_ids[0], 2)]


def map_overlay_sprite_ids(data, model, x, y):
    tile = map_model.tile_summary(data, model, x, y)
    battle_feature = tile["battle_feature_id"]
    city_resource = tile["city_resource_id"]
    road_id = tile["road_connection_tile_id"]
    bridge_id = tile["bridge_variant_id"]
    wall_id = tile["long_wall_or_battle_bonus_mode"]

    if battle_feature >= 0:
        yield "battle_resource", "ground", GROUND_RESOURCE_BASE + battle_feature, -8
    if city_resource >= 0:
        yield "city_resource", "resource", city_resource, -18
    if road_id >= 0:
        road_kind = tile["road_overlay_kind"]
        height_bucket = ROAD_HEIGHT_MODE_BY_DETAIL[tile["terrain_detail_mode"]]
        yield "road", "make", road_kind * 0x51 + road_id, -ROAD_HEIGHT_DRAW_Y[height_bucket]
    if bridge_id >= 0:
        yield "bridge_probe", "make", 0x3CC // 4 + bridge_id, 0
    if wall_id >= 0:
        yield "long_wall_probe", "road", 214 + wall_id, -5
    if tile["linked_city_or_object_ptr"] != 0:
        yield "city_link", "city", 0, -104


def city_sprite_id(city):
    level = city.get("city_sprite_level_from_population", city.get("city_sprite_level", 0))
    if level < 0:
        level = 0
    # CITY.EMG is arranged in three style blocks of eight levels. Current
    # large-map evidence confirms the bank, while exact culture/style selection
    # still needs more samples; block 0 matches the small house seen in SAVE01.
    return max(0, min(level, 7))


def draw_group(groups, pixels, canvas_width, canvas_height, sprite_id, x, y, color_mode):
    if sprite_id < 0 or sprite_id >= len(groups):
        return False
    emg_sprites.draw_sprite(
        pixels,
        canvas_width,
        canvas_height,
        groups[sprite_id],
        x,
        y,
        color_mode=color_mode,
    )
    return True


def iter_visible_tiles(view_x, view_y, view_width, view_height, origin_x, origin_y):
    tile_step_x = 48
    tile_step_y = 24
    for diag in range(view_width + view_height - 1):
        min_dx = max(0, diag - (view_height - 1))
        max_dx = min(view_width - 1, diag)
        for dx in range(min_dx, max_dx + 1):
            dy = diag - dx
            map_x = view_x + dx
            map_y = view_y + dy
            draw_x = origin_x + (dx - dy) * tile_step_x
            draw_y = origin_y + (dx + dy) * tile_step_y - 40
            yield map_x, map_y, draw_x, draw_y


def render_sprite_map(data, model, sprite_banks, viewport, color_mode, layers, city_records=None):
    view_x, view_y, view_width, view_height = clamp_viewport(model, viewport)
    tile_step_x = 48
    tile_step_y = 24
    max_sprite_right = 96
    max_sprite_bottom = 180
    canvas_width = (view_width + view_height - 1) * tile_step_x + max_sprite_right
    canvas_height = (view_width + view_height - 1) * tile_step_y + max_sprite_bottom
    origin_x = (view_height - 1) * tile_step_x
    origin_y = 0
    pixels = bytearray([0, 0, 0] * canvas_width * canvas_height)
    ground_groups = sprite_banks["ground"]["groups"]
    draw_details = "details" in layers
    city_by_tile = {}
    if "city" in layers and city_records:
        for city in city_records:
            if city.get("valid_position"):
                city_by_tile.setdefault((city["x"], city["y"]), []).append(city)

    visible_tiles = list(iter_visible_tiles(view_x, view_y, view_width, view_height, origin_x, origin_y))

    for map_x, map_y, draw_x, draw_y in visible_tiles:
        sprite_id = terrain_sprite_id(data, model, map_x, map_y)
        draw_group(ground_groups, pixels, canvas_width, canvas_height, sprite_id, draw_x, draw_y, color_mode)

    if draw_details:
        for map_x, map_y, draw_x, draw_y in visible_tiles:
            for detail_sprite_id, detail_y_adjust in terrain_detail_sprite_ids(data, model, map_x, map_y):
                draw_group(
                    ground_groups,
                    pixels,
                    canvas_width,
                    canvas_height,
                    detail_sprite_id,
                    draw_x,
                    draw_y + detail_y_adjust,
                    color_mode,
                )

    for map_x, map_y, draw_x, draw_y in visible_tiles:
        for layer, bank_name, overlay_sprite_id, y_adjust in map_overlay_sprite_ids(data, model, map_x, map_y):
            if layer not in layers:
                continue
            draw_group(
                sprite_banks[bank_name]["groups"],
                pixels,
                canvas_width,
                canvas_height,
                overlay_sprite_id,
                draw_x,
                draw_y + y_adjust,
                color_mode,
            )

    if "city" in layers:
        for map_x, map_y, draw_x, draw_y in visible_tiles:
            for city in city_by_tile.get((map_x, map_y), []):
                draw_group(
                    sprite_banks["city"]["groups"],
                    pixels,
                    canvas_width,
                    canvas_height,
                    city_sprite_id(city),
                    draw_x - 18,
                    draw_y - 104,
                    color_mode,
                )
    return canvas_width, canvas_height, pixels, (view_x, view_y, view_width, view_height)


def parse_layers(raw):
    aliases = {
        "terrain": ["details"],
        "resources": ["battle_resource", "city_resource"],
        "roads": ["road"],
        "road_probe": ["road_probe", "bridge_probe", "long_wall_probe"],
        "roads_probe": ["road_probe", "bridge_probe", "long_wall_probe"],
        "cities": ["city"],
        "objects": ["battle_resource", "city_resource", "city"],
        "all": ["details", "battle_resource", "city_resource", "road", "city"],
    }
    layers = set()
    for part in raw.split(","):
        name = part.strip().lower()
        if not name:
            continue
        for expanded in aliases.get(name, [name]):
            layers.add(expanded)
    valid = set(aliases["all"]) | set(aliases["road_probe"])
    valid.update(aliases["roads"])
    unknown = sorted(layers - valid)
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown layer(s): {', '.join(unknown)}")
    return layers


def default_output_path(map_path, overlay):
    relative = map_path.relative_to(ROOT)
    safe = "_".join(relative.with_suffix("").parts)
    return DEFAULT_OUT_DIR / f"{safe}_{overlay}.png"


def main():
    parser = argparse.ArgumentParser(description="Export a simple MAP terrain preview PNG.")
    parser.add_argument("map", nargs="?", default="Save/WORLD_FLAT.MAP", help="Path to a .MAP file")
    parser.add_argument("--mode", choices=["sprite", "color"], default="sprite")
    parser.add_argument("--overlay", choices=["terrain", "resources", "owner", "all"], default="terrain")
    parser.add_argument("--scale", type=int, default=2, help="Nearest-neighbor tile scale")
    parser.add_argument("--viewport", type=parse_viewport, help="Tile viewport as x,y,width,height")
    parser.add_argument("--color-mode", choices=["565", "555"], default="565", help="Source sprite 16-bit RGB layout")
    parser.add_argument(
        "--layers",
        type=parse_layers,
        default=parse_layers("terrain"),
        help="Sprite overlay layers: terrain, resources, cities, objects, all, road_probe",
    )
    parser.add_argument(
        "--map-resource-manifest",
        help="Modern map resource manifest. Defaults to generated manifest when present.",
    )
    parser.add_argument("--no-details", action="store_true", help="Skip terrain detail overlay sprites")
    parser.add_argument("--out", help="Output PNG path")
    args = parser.parse_args()

    if args.scale < 1 or args.scale > 16:
        raise SystemExit("--scale must be between 1 and 16")

    map_path = parse_map_path(args.map)
    data, model = map_model.load_map(map_path)
    suffix = args.overlay if args.mode == "color" else f"sprite_{args.color_mode}"
    out_path = Path(args.out) if args.out else default_output_path(map_path, suffix)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    viewport = None
    if args.mode == "sprite":
        manifest = map_resources.load_manifest(args.map_resource_manifest)
        layers = set(args.layers)
        if args.no_details:
            layers.discard("details")
        bank_paths = {bank["id"]: bank["source_path"] for bank in manifest["banks"]}
        sprite_banks = {"ground": emg_sprites.parse_emg(bank_paths.get("ground", NEW_GROUND_EMG))}
        if {"road", "bridge_probe"} & layers:
            sprite_banks["make"] = emg_sprites.parse_emg(bank_paths.get("make", MAKE_EMG))
        if {"road_probe", "long_wall_probe"} & layers:
            sprite_banks["road"] = emg_sprites.parse_emg(bank_paths.get("road", ROAD_EMG))
        if "city" in layers:
            sprite_banks["city"] = emg_sprites.parse_emg(bank_paths.get("city", CITY_EMG))
        if "city_resource" in layers:
            sprite_banks["resource"] = emg_sprites.parse_emg(bank_paths.get("resource", RESOURCE_EMG))
        city_records = None
        if "city" in layers:
            city_records = map_model.parse_save_tail_cities(data, model)["cities"]
        width, height, pixels, viewport = render_sprite_map(
            data,
            model,
            sprite_banks,
            args.viewport,
            args.color_mode,
            layers,
            city_records=city_records,
        )
    else:
        width, height, pixels = render_preview(data, model, args.scale, args.overlay)

    png_writer.write_png_rgb(out_path, width, height, pixels)
    print(f"wrote {out_path}")
    viewport_text = f" viewport={viewport}" if viewport else ""
    detail_text = "" if args.mode != "sprite" else f" layers={','.join(sorted(layers))}"
    print(f"source={map_path.relative_to(ROOT).as_posix()} size={model['width']}x{model['height']} output={width}x{height} mode={args.mode}{detail_text}{viewport_text}")


if __name__ == "__main__":
    main()

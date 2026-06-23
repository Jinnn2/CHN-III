#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path

import emg_sprites
import png_writer


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "remake-workbench" / "output" / "modern_map"

TILE_STEP_X = 48
TILE_STEP_Y = 24
TILE_TOP_Y = -40
TILE_W = 96
TILE_H = 48

NEW_GROUND_EMG = ROOT / "EMG" / "NEW_GROUND.EMG"
MAKE_EMG = ROOT / "EMG" / "MAKE.EMG"


TERRAIN = {
    "grass": (115, 166, 88),
    "plain": (148, 178, 98),
    "forest": (62, 124, 78),
    "hill": (132, 132, 96),
    "marsh": (92, 142, 118),
    "sand": (194, 180, 112),
}

TERRAIN_SPRITES = {
    "grass": [28, 20, 37, 21, 5, 46, 30, 6],
    "plain": [71, 11, 69, 33, 12, 79, 51, 77],
    "forest": [925, 918, 935, 943, 949, 944, 945, 959],
    "hill": [1044, 1043, 1042, 980, 1040, 1025, 1027, 978],
    "marsh": [1414, 1405, 1417, 1410, 1379, 1407, 1367],
    "sand": [1572, 1537, 1541, 1574, 1562, 1553, 1560, 1542],
    "water": [1320, 1321, 1309, 1305, 1342, 1304, 1307, 1318],
}

ROAD_SPRITES = {
    "dirt": {
        "isolated": 0,
        "endpoint": 1,
        "straight": 2,
        "curve": 4,
        "branch": 18,
        "cross": 36,
    },
    "stone": {
        "isolated": 40,
        "endpoint": 41,
        "straight": 42,
        "curve": 44,
        "branch": 58,
        "cross": 76,
    },
}


def blend(a, b, amount):
    return tuple(int(round(a[i] * (1.0 - amount) + b[i] * amount)) for i in range(3))


def put_pixel(pixels, width, height, x, y, color):
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    pos = (y * width + x) * 3
    pixels[pos:pos + 3] = bytes(color)


def fill_diamond(pixels, width, height, cx, cy, color):
    top = cy + TILE_TOP_Y
    half_w = TILE_W // 2
    half_h = TILE_H // 2
    center_y = top + half_h
    for yy in range(top, top + TILE_H + 1):
        distance = abs(yy - center_y)
        span = int(half_w * (1.0 - distance / half_h))
        shade = 0.06 if yy < center_y else -0.04
        shaded = blend(color, (255, 255, 255), shade) if shade > 0 else blend(color, (0, 0, 0), -shade)
        for xx in range(cx - span, cx + span + 1):
            put_pixel(pixels, width, height, xx, yy, shaded)


def draw_disc(pixels, width, height, cx, cy, radius, color):
    r2 = radius * radius
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                put_pixel(pixels, width, height, x, y, color)


def draw_line(pixels, width, height, x0, y0, x1, y1, radius, color):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    for step in range(steps + 1):
        t = step / steps
        x = int(round(x0 + dx * t))
        y = int(round(y0 + dy * t))
        draw_disc(pixels, width, height, x, y, radius, color)


def lighten_height(base, x, y, height):
    wave = math.sin((x * 0.9 + y * 0.55) * 0.8) * 0.04
    if height > 0:
        return blend(base, (255, 244, 196), min(0.18, height * 0.05 + wave))
    if height < 0:
        return blend(base, (62, 112, 124), min(0.18, abs(height) * 0.05 - wave))
    return base


def tile_to_screen(x, y, origin_x, origin_y):
    return (
        origin_x + (x - y) * TILE_STEP_X,
        origin_y + (x + y) * TILE_STEP_Y,
    )


def edge_midpoint(x, y, direction, origin_x, origin_y):
    cx, cy = tile_to_screen(x, y, origin_x, origin_y)
    top = cy + TILE_TOP_Y
    if direction == "ne":
        return cx + TILE_W // 4, top + TILE_H // 4
    if direction == "se":
        return cx + TILE_W // 4, top + TILE_H * 3 // 4
    if direction == "sw":
        return cx - TILE_W // 4, top + TILE_H * 3 // 4
    if direction == "nw":
        return cx - TILE_W // 4, top + TILE_H // 4
    return cx, top + TILE_H // 2


def node_screen(node, origin_x, origin_y):
    x = node["x"]
    y = node["y"]
    cx, cy = tile_to_screen(x, y, origin_x, origin_y)
    return cx + int(round(node.get("offset_x", 0) * TILE_STEP_X)), cy + int(round(node.get("offset_y", 0) * TILE_STEP_Y))


def make_demo_map():
    width = 30
    height = 24
    tiles = []
    for y in range(height):
        row = []
        for x in range(width):
            h = int(round(2.0 * math.sin(x * 0.33) + 1.4 * math.cos(y * 0.41)))
            if y > 17 and x < 8:
                terrain = "sand"
            elif (x - 7) * (x - 7) + (y - 8) * (y - 8) < 20:
                terrain = "forest"
            elif h >= 3:
                terrain = "hill"
            elif y > 13 and 15 < x < 25:
                terrain = "marsh"
            else:
                terrain = "plain" if (x + y) % 4 else "grass"
            sprites = TERRAIN_SPRITES[terrain]
            row.append({
                "terrain": terrain,
                "height": h,
                "sprite_bank": "ground",
                "sprite_id": sprites[(x * 3 + y * 5) % len(sprites)],
            })
        tiles.append(row)

    cities = [
        {"id": "capital", "name": "Jingzhou", "x": 8, "y": 9, "size": 3},
        {"id": "riverport", "name": "Hekou", "x": 17, "y": 8, "size": 2},
        {"id": "southpost", "name": "Nanling", "x": 20, "y": 16, "size": 2},
        {"id": "westgate", "name": "Xiguan", "x": 5, "y": 17, "size": 1},
    ]

    roads = [
        {
            "id": "imperial-road",
            "kind": "stone",
            "width": 5,
            "nodes": [
                {"x": 5, "y": 17},
                {"x": 7, "y": 14},
                {"x": 8, "y": 9},
                {"x": 11, "y": 8},
                {"x": 17, "y": 8},
                {"x": 20, "y": 10},
                {"x": 20, "y": 16},
            ],
        },
        {
            "id": "north-branch",
            "kind": "dirt",
            "width": 3,
            "nodes": [
                {"x": 8, "y": 9},
                {"x": 9, "y": 6},
                {"x": 12, "y": 4},
                {"x": 16, "y": 3},
            ],
        },
        {
            "id": "east-branch",
            "kind": "dirt",
            "width": 3,
            "nodes": [
                {"x": 17, "y": 8},
                {"x": 21, "y": 7},
                {"x": 25, "y": 9},
            ],
        },
    ]

    rivers = [
        {
            "id": "main-river",
            "kind": "river",
            "width": 9,
            "nodes": [
                {"x": 2, "y": 3, "offset_y": -0.2},
                {"x": 5, "y": 5},
                {"x": 8, "y": 7},
                {"x": 11, "y": 7},
                {"x": 14, "y": 9},
                {"x": 17, "y": 8},
                {"x": 20, "y": 9},
                {"x": 23, "y": 12},
                {"x": 27, "y": 14},
            ],
        },
        {
            "id": "south-creek",
            "kind": "creek",
            "width": 5,
            "nodes": [
                {"x": 11, "y": 14},
                {"x": 14, "y": 13},
                {"x": 16, "y": 14},
                {"x": 20, "y": 16},
                {"x": 24, "y": 17},
            ],
        },
    ]

    return {
        "schema_version": 1,
        "map": {"width": width, "height": height, "projection": "isometric_diamond"},
        "tiles": tiles,
        "layers": {
            "river_networks": rivers,
            "road_networks": roads,
            "cities": cities,
        },
        "rendering": {
            "network_rule": "roads and rivers are continuous polylines over tile anchors; per-tile masks can be derived for gameplay, but rendering is not limited to original tile sprite ids",
            "texture_resources": {
                "terrain_and_river_surfaces": "EMG/NEW_GROUND.EMG",
                "road_overlays": "EMG/MAKE.EMG groups 0..80",
            },
            "layer_order": ["terrain", "rivers", "roads", "cities"],
        },
    }


def derive_tile_connections(data):
    width = data["map"]["width"]
    height = data["map"]["height"]
    connections = {
        "roads": [[0 for _ in range(width)] for _ in range(height)],
        "rivers": [[0 for _ in range(width)] for _ in range(height)],
    }
    road_kinds = [[None for _ in range(width)] for _ in range(height)]
    river_kinds = [[None for _ in range(width)] for _ in range(height)]
    bit_by_delta = {
        (0, -1): 1,
        (1, 0): 2,
        (0, 1): 4,
        (-1, 0): 8,
        (1, -1): 16,
        (-1, 1): 32,
    }
    for layer_name, source_name, kinds in (
        ("roads", "road_networks", road_kinds),
        ("rivers", "river_networks", river_kinds),
    ):
        for network in data["layers"][source_name]:
            nodes = network["nodes"]
            for a, b in zip(nodes, nodes[1:]):
                ax, ay = a["x"], a["y"]
                bx, by = b["x"], b["y"]
                dx = 0 if bx == ax else (1 if bx > ax else -1)
                dy = 0 if by == ay else (1 if by > ay else -1)
                x, y = ax, ay
                while (x, y) != (bx, by):
                    nx = x + dx if x != bx else x
                    ny = y + dy if y != by else y
                    bit = bit_by_delta.get((nx - x, ny - y), 0)
                    back = bit_by_delta.get((x - nx, y - ny), 0)
                    if 0 <= x < width and 0 <= y < height:
                        connections[layer_name][y][x] |= bit
                        kinds[y][x] = network["kind"]
                    if 0 <= nx < width and 0 <= ny < height:
                        connections[layer_name][ny][nx] |= back
                        kinds[ny][nx] = network["kind"]
                    x, y = nx, ny
    data["derived"] = {
        "tile_connection_masks": connections,
        "tile_network_kinds": {
            "roads": road_kinds,
            "rivers": river_kinds,
        },
    }


def ground_draw_base(cx, cy):
    return cx - 48, cy - 80


def draw_emg_sprite(pixels, canvas_width, canvas_height, bank, sprite_id, cx, cy):
    x, y = ground_draw_base(cx, cy)
    emg_sprites.draw_sprite(pixels, canvas_width, canvas_height, bank["groups"][sprite_id], x, y)


def sprite_from_terrain(tile, x, y):
    explicit = tile.get("sprite_id")
    if explicit is not None:
        return explicit
    sprites = TERRAIN_SPRITES[tile["terrain"]]
    return sprites[(x * 3 + y * 5) % len(sprites)]


def river_surface_sprite(x, y, kind):
    sprites = TERRAIN_SPRITES["water"]
    salt = 11 if kind == "creek" else 0
    return sprites[(x * 7 + y * 3 + salt) % len(sprites)]


def road_sprite_class(mask):
    degree = mask.bit_count()
    if degree == 0:
        return "isolated"
    if degree == 1:
        return "endpoint"
    if degree >= 4:
        return "cross"
    if degree == 3:
        return "branch"
    opposite_pairs = [(1, 4), (2, 8), (16, 32)]
    if any(mask & a and mask & b for a, b in opposite_pairs):
        return "straight"
    return "curve"


def road_sprite_id(mask, kind):
    style = ROAD_SPRITES.get(kind, ROAD_SPRITES["dirt"])
    return style[road_sprite_class(mask)]


def draw_network(pixels, canvas_width, canvas_height, network, origin_x, origin_y, palette):
    color = palette[network["kind"]]
    outline = blend(color, (0, 0, 0), 0.45)
    radius = max(1, network.get("width", 3) // 2)
    points = [node_screen(node, origin_x, origin_y) for node in network["nodes"]]
    for a, b in zip(points, points[1:]):
        draw_line(pixels, canvas_width, canvas_height, a[0], a[1], b[0], b[1], radius + 1, outline)
    for a, b in zip(points, points[1:]):
        draw_line(pixels, canvas_width, canvas_height, a[0], a[1], b[0], b[1], radius, color)
    for x, y in points:
        draw_disc(pixels, canvas_width, canvas_height, x, y, radius, color)


def render_procedural(data):
    width = data["map"]["width"]
    height = data["map"]["height"]
    canvas_width = (width + height - 1) * TILE_STEP_X + TILE_W
    canvas_height = (width + height - 1) * TILE_STEP_Y + TILE_H + 80
    origin_x = (height - 1) * TILE_STEP_X + TILE_W // 2
    origin_y = 48
    pixels = bytearray([18, 22, 24] * canvas_width * canvas_height)

    for diag in range(width + height - 1):
        min_x = max(0, diag - (height - 1))
        max_x = min(width - 1, diag)
        for x in range(min_x, max_x + 1):
            y = diag - x
            tile = data["tiles"][y][x]
            cx, cy = tile_to_screen(x, y, origin_x, origin_y)
            base = TERRAIN[tile["terrain"]]
            fill_diamond(pixels, canvas_width, canvas_height, cx, cy, lighten_height(base, x, y, tile["height"]))

    river_palette = {"river": (58, 151, 184), "creek": (82, 174, 194)}
    road_palette = {"stone": (116, 104, 82), "dirt": (178, 139, 76)}
    for river in data["layers"]["river_networks"]:
        draw_network(pixels, canvas_width, canvas_height, river, origin_x, origin_y, river_palette)
    for road in data["layers"]["road_networks"]:
        draw_network(pixels, canvas_width, canvas_height, road, origin_x, origin_y, road_palette)

    for city in data["layers"]["cities"]:
        cx, cy = tile_to_screen(city["x"], city["y"], origin_x, origin_y)
        radius = 5 + city["size"] * 3
        draw_disc(pixels, canvas_width, canvas_height, cx, cy - 8, radius + 2, (40, 38, 32))
        draw_disc(pixels, canvas_width, canvas_height, cx, cy - 8, radius, (204, 184, 114))
        draw_disc(pixels, canvas_width, canvas_height, cx - 3, cy - 11, max(2, radius // 3), (92, 72, 58))

    return canvas_width, canvas_height, pixels


def render_textured(data):
    width = data["map"]["width"]
    height = data["map"]["height"]
    canvas_width = (width + height - 1) * TILE_STEP_X + TILE_W
    canvas_height = (width + height - 1) * TILE_STEP_Y + TILE_H + 120
    origin_x = (height - 1) * TILE_STEP_X + TILE_W // 2
    origin_y = 48
    pixels = bytearray([0, 0, 0] * canvas_width * canvas_height)
    ground_bank = emg_sprites.parse_emg(NEW_GROUND_EMG)
    make_bank = emg_sprites.parse_emg(MAKE_EMG)
    river_masks = data["derived"]["tile_connection_masks"]["rivers"]
    road_masks = data["derived"]["tile_connection_masks"]["roads"]
    river_kinds = data["derived"]["tile_network_kinds"]["rivers"]
    road_kinds = data["derived"]["tile_network_kinds"]["roads"]

    for diag in range(width + height - 1):
        min_x = max(0, diag - (height - 1))
        max_x = min(width - 1, diag)
        for x in range(min_x, max_x + 1):
            y = diag - x
            cx, cy = tile_to_screen(x, y, origin_x, origin_y)
            sprite_id = sprite_from_terrain(data["tiles"][y][x], x, y)
            draw_emg_sprite(pixels, canvas_width, canvas_height, ground_bank, sprite_id, cx, cy)

    for diag in range(width + height - 1):
        min_x = max(0, diag - (height - 1))
        max_x = min(width - 1, diag)
        for x in range(min_x, max_x + 1):
            y = diag - x
            if not river_masks[y][x]:
                continue
            cx, cy = tile_to_screen(x, y, origin_x, origin_y)
            sprite_id = river_surface_sprite(x, y, river_kinds[y][x])
            draw_emg_sprite(pixels, canvas_width, canvas_height, ground_bank, sprite_id, cx, cy)

    # A continuous underlay keeps modern networks connected even when a legacy
    # road sprite category is only an approximation for this generated graph.
    river_palette = {"river": (58, 151, 184), "creek": (82, 174, 194)}
    road_palette = {"stone": (116, 104, 82), "dirt": (178, 139, 76)}
    for river in data["layers"]["river_networks"]:
        draw_network(pixels, canvas_width, canvas_height, river, origin_x, origin_y, river_palette)
    for road in data["layers"]["road_networks"]:
        draw_network(pixels, canvas_width, canvas_height, road, origin_x, origin_y, road_palette)

    for diag in range(width + height - 1):
        min_x = max(0, diag - (height - 1))
        max_x = min(width - 1, diag)
        for x in range(min_x, max_x + 1):
            y = diag - x
            mask = road_masks[y][x]
            if not mask:
                continue
            cx, cy = tile_to_screen(x, y, origin_x, origin_y)
            sprite_id = road_sprite_id(mask, road_kinds[y][x])
            draw_emg_sprite(pixels, canvas_width, canvas_height, make_bank, sprite_id, cx, cy)

    for city in data["layers"]["cities"]:
        cx, cy = tile_to_screen(city["x"], city["y"], origin_x, origin_y)
        radius = 5 + city["size"] * 3
        draw_disc(pixels, canvas_width, canvas_height, cx, cy - 8, radius + 2, (40, 38, 32))
        draw_disc(pixels, canvas_width, canvas_height, cx, cy - 8, radius, (204, 184, 114))
        draw_disc(pixels, canvas_width, canvas_height, cx - 3, cy - 11, max(2, radius // 3), (92, 72, 58))

    return canvas_width, canvas_height, pixels


def main():
    parser = argparse.ArgumentParser(description="Generate and render a modern connected road/river map sample.")
    parser.add_argument("--json-out", default=OUT_DIR / "modern_connected_map.json")
    parser.add_argument("--png-out", default=OUT_DIR / "modern_connected_map_textured.png")
    parser.add_argument("--render-mode", choices=["textured", "procedural"], default="textured")
    args = parser.parse_args()

    data = make_demo_map()
    derive_tile_connections(data)

    json_path = Path(args.json_out)
    png_path = Path(args.png_out)
    if not json_path.is_absolute():
        json_path = ROOT / json_path
    if not png_path.is_absolute():
        png_path = ROOT / png_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.render_mode == "textured":
        width, height, pixels = render_textured(data)
    else:
        width, height, pixels = render_procedural(data)
    png_writer.write_png_rgb(png_path, width, height, pixels)
    print(f"wrote {json_path}")
    print(f"wrote {png_path}")
    print(f"map={data['map']['width']}x{data['map']['height']} roads={len(data['layers']['road_networks'])} rivers={len(data['layers']['river_networks'])}")


if __name__ == "__main__":
    main()

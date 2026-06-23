#!/usr/bin/env python3
from pathlib import Path

import emg_sprites
import export_terrain_preview
import map_model


ROOT = Path(__file__).resolve().parents[2]


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def iter_map_paths():
    for path in sorted((ROOT / "Save").glob("*.MAP")):
        if path.with_suffix(".MGI").exists():
            yield path


def check_detail_sprites(groups):
    highest_sprite_id = -1
    detail_draw_count = 0
    for path in iter_map_paths():
        data, model = map_model.load_map(path)
        for y in range(model["height"]):
            for x in range(model["width"]):
                for sprite_id, _ in export_terrain_preview.terrain_detail_sprite_ids(data, model, x, y):
                    highest_sprite_id = max(highest_sprite_id, sprite_id)
                    detail_draw_count += 1
                    if sprite_id >= len(groups):
                        raise AssertionError(f"{path} tile {x},{y} detail sprite {sprite_id} is outside NEW_GROUND")
    return detail_draw_count, highest_sprite_id


def check_layer_sprites(ground_groups, road_groups, city_groups, resource_groups):
    counts = {
        "battle_resource_draws": 0,
        "city_resource_draws": 0,
        "road_draws": 0,
        "bridge_draws": 0,
        "long_wall_draws": 0,
        "city_marker_draws": 0,
    }
    highest = {key: -1 for key in counts}
    for path in iter_map_paths():
        data, model = map_model.load_map(path)
        for y in range(model["height"]):
            for x in range(model["width"]):
                for layer, bank_name, sprite_id, _ in export_terrain_preview.map_overlay_sprite_ids(
                    data, model, x, y
                ):
                    key = f"{layer}_draws"
                    counts[key] += 1
                    highest[key] = max(highest[key], sprite_id)
                    bank = {
                        "ground": ground_groups,
                        "road": road_groups,
                        "city": city_groups,
                        "resource": resource_groups,
                    }[bank_name]
                    if sprite_id >= len(bank):
                        raise AssertionError(
                            f"{path} tile {x},{y} {layer} sprite {sprite_id} is outside {bank_name}"
                        )
    return counts, highest


def main():
    bank = emg_sprites.parse_emg("EMG/NEW_GROUND.EMG")
    road_bank = emg_sprites.parse_emg("EMG/ROAD.EMG")
    city_bank = emg_sprites.parse_emg("EMG/CITY.EMG")
    resource_bank = emg_sprites.parse_emg("EMG/RESOURCE.EMG")
    assert_equal(bank["group_count"], 5127, "NEW_GROUND group count")
    assert_equal(road_bank["group_count"], 236, "ROAD group count")
    assert_equal(city_bank["group_count"], 32, "CITY group count")
    assert_equal(resource_bank["group_count"], 43, "RESOURCE group count")
    for sprite_id in [0, 73, 1379, 1382, 4373, 4457, 5123, 5124, 5125]:
        sprite = bank["groups"][sprite_id]
        if sprite["pixel_count"] <= 0:
            raise AssertionError(f"sprite {sprite_id}: empty pixel data")
        width, height = emg_sprites.sprite_dimensions(sprite)
        if width <= 0 or height <= 0:
            raise AssertionError(f"sprite {sprite_id}: invalid dimensions {width}x{height}")
    detail_draw_count, highest_detail_sprite = check_detail_sprites(bank["groups"])
    layer_counts, layer_highest = check_layer_sprites(
        bank["groups"], road_bank["groups"], city_bank["groups"], resource_bank["groups"]
    )
    print(
        f"checked NEW_GROUND.EMG: {bank['group_count']} sprite groups; "
        f"detail_draws={detail_draw_count} highest_detail_sprite={highest_detail_sprite}"
    )
    print(
        "checked map overlay layers: "
        + " ".join(f"{key}={value}" for key, value in sorted(layer_counts.items()))
        + " "
        + " ".join(f"highest_{key}={value}" for key, value in sorted(layer_highest.items()))
    )


if __name__ == "__main__":
    main()

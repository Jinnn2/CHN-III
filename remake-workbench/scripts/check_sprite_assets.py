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


def check_layer_sprites(ground_groups, make_groups, road_groups, city_groups, resource_groups):
    counts = {
        "battle_resource_draws": 0,
        "city_resource_draws": 0,
        "road_draws": 0,
        "road_probe_draws": 0,
        "bridge_probe_draws": 0,
        "long_wall_probe_draws": 0,
        "city_link_draws": 0,
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
                    if key not in counts:
                        continue
                    counts[key] += 1
                    highest[key] = max(highest[key], sprite_id)
                    bank = {
                        "ground": ground_groups,
                        "make": make_groups,
                        "road": road_groups,
                        "city": city_groups,
                        "resource": resource_groups,
                    }[bank_name]
                    if sprite_id >= len(bank):
                        raise AssertionError(
                            f"{path} tile {x},{y} {layer} sprite {sprite_id} is outside {bank_name}"
                        )
    return counts, highest


def check_save_tail_cities():
    path = ROOT / "Save" / "SAVE00" / "SAVE.MAP"
    data, model = map_model.load_map(path)
    result = map_model.parse_save_tail_cities(data, model)
    if result["status"] != "ok":
        raise AssertionError(f"SAVE00 city tail parse status is {result['status']}")
    if result["city_record_count"] <= 0:
        raise AssertionError("SAVE00 city tail parse found no cities")
    invalid = [city for city in result["cities"] if not city["valid_position"]]
    if invalid:
        raise AssertionError(f"SAVE00 city tail parse found invalid positions: {invalid[:3]}")
    return result


def check_controlled_road_sample():
    path = ROOT / "Save" / "save.MAP"
    if not path.exists():
        return None
    data, model = map_model.load_map(path)
    positive = []
    for y in range(model["height"]):
        for x in range(model["width"]):
            tile = map_model.tile_summary(data, model, x, y)
            if (
                tile["road_connection_tile_id"] >= 0
                or tile["bridge_variant_id"] >= 0
                or tile["long_wall_or_battle_bonus_mode"] >= 0
            ):
                positive.append(tile)
    if not positive:
        raise AssertionError("controlled road sample exists but has no positive road tiles")
    road_ids = [tile["road_connection_tile_id"] for tile in positive if tile["road_connection_tile_id"] >= 0]
    road_kinds = {tile["road_overlay_kind"] for tile in positive if tile["road_connection_tile_id"] >= 0}
    road_sprite_ids = [
        tile["road_overlay_kind"] * 0x51 + tile["road_connection_tile_id"]
        for tile in positive
        if tile["road_connection_tile_id"] >= 0
    ]
    if max(road_sprite_ids) >= 321:
        raise AssertionError(f"controlled road sample road sprite outside MAKE.EMG: {max(road_sprite_ids)}")
    mismatches = []
    for tile in positive:
        if tile["road_connection_tile_id"] < 0:
            continue
        decoded = map_model.decode_road_connection_id(data, model, tile["x"], tile["y"])
        if decoded != tile["road_connection_tile_id"]:
            mismatches.append((tile["x"], tile["y"], tile["road_connection_tile_id"], decoded))
    if mismatches:
        raise AssertionError(f"Decode_Road mismatch in controlled sample: {mismatches[:5]}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "positive_tiles": len(positive),
        "road_tiles": len(road_ids),
        "road_kind_values": sorted(road_kinds),
        "highest_road_group": max(road_ids) if road_ids else -1,
        "highest_make_road_group": max(road_sprite_ids) if road_sprite_ids else -1,
        "decode_road_mismatches": len(mismatches),
        "bridge_tiles": sum(1 for tile in positive if tile["bridge_variant_id"] >= 0),
        "long_wall_tiles": sum(1 for tile in positive if tile["long_wall_or_battle_bonus_mode"] >= 0),
    }


def main():
    bank = emg_sprites.parse_emg("EMG/NEW_GROUND.EMG")
    make_bank = emg_sprites.parse_emg("EMG/MAKE.EMG")
    road_bank = emg_sprites.parse_emg("EMG/ROAD.EMG")
    city_bank = emg_sprites.parse_emg("EMG/CITY.EMG")
    resource_bank = emg_sprites.parse_emg("EMG/RESOURCE.EMG")
    assert_equal(bank["group_count"], 5127, "NEW_GROUND group count")
    assert_equal(make_bank["group_count"], 321, "MAKE group count")
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
        bank["groups"], make_bank["groups"], road_bank["groups"], city_bank["groups"], resource_bank["groups"]
    )
    city_result = check_save_tail_cities()
    road_sample = check_controlled_road_sample()
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
    print(
        f"checked SAVE00 city tail: cities={city_result['city_record_count']} "
        f"stride=0x{city_result['city_record_stride']:x}"
    )
    if road_sample:
        print(
            "checked controlled road sample: "
            f"tiles={road_sample['positive_tiles']} road_tiles={road_sample['road_tiles']} "
            f"kinds={road_sample['road_kind_values']} highest_road_group={road_sample['highest_road_group']} "
            f"highest_make_road_group={road_sample['highest_make_road_group']} "
            f"decode_mismatches={road_sample['decode_road_mismatches']} "
            f"bridge_tiles={road_sample['bridge_tiles']} long_wall_tiles={road_sample['long_wall_tiles']}"
        )


if __name__ == "__main__":
    main()

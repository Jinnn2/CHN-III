#!/usr/bin/env python3
from pathlib import Path

import map_model


ROOT = Path(__file__).resolve().parents[2]
MAP_DIR = ROOT / "Save"


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises(exc_type, fn, label):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"{label}: expected {exc_type.__name__}")


def check_one_map(path):
    data, model = map_model.load_map(path)
    mode = model["map_size_mode"]
    expected = map_model.MAP_SIZE_MODES[mode]
    assert_equal(model["width"], expected["width"], f"{path} width")
    assert_equal(model["height"], expected["height"], f"{path} height")
    assert_equal(model["tile_count"], expected["width"] * expected["height"], f"{path} tile_count")
    assert_equal(model["land_offset"], sum(size for _, size in map_model.STATIC_MAP_PREFIX_BLOCKS), f"{path} land_offset")
    assert_equal(model["land_bytes"], model["tile_count"] * 0x100, f"{path} land_bytes")
    if len(data) < model["tail_offset"]:
        raise AssertionError(f"{path}: tail offset beyond decompressed stream")

    first = map_model.tile_summary(data, model, 0, 0)
    last = map_model.tile_summary(data, model, model["width"] - 1, model["height"] - 1)
    assert_equal(first["index"], 0, f"{path} first index")
    assert_equal(last["index"], model["tile_count"] - 1, f"{path} last index")

    if model["scenario"]["horizontal_wrap_setting"] == 1:
        wrapped_left = map_model.tile_summary(data, model, -1, 0)
        wrapped_right = map_model.tile_summary(data, model, model["width"], 0)
        assert_equal(wrapped_left["x"], model["width"] - 1, f"{path} wrap -1 x")
        assert_equal(wrapped_right["x"], 0, f"{path} wrap width x")

    assert_raises(
        IndexError,
        lambda: map_model.tile_offset(model, -1, 0, wrap=False),
        f"{path} no-wrap negative x",
    )
    assert_raises(
        IndexError,
        lambda: map_model.tile_offset(model, 0, model["height"]),
        f"{path} y overflow",
    )
    return mode


def main():
    modes = set()
    paths = sorted(MAP_DIR.rglob("*.MAP"))
    if not paths:
        raise AssertionError("no MAP files found")
    for path in paths:
        modes.add(check_one_map(path))
    assert_equal(modes, set(map_model.MAP_SIZE_MODES), "covered map size modes")
    print(f"checked {len(paths)} MAP files; modes covered: {sorted(modes)}")


if __name__ == "__main__":
    main()

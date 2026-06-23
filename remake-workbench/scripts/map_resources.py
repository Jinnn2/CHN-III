#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import emg_sprites


ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "remake-workbench" / "output" / "map_resources"
MANIFEST_DIR = OUT_ROOT / "manifests"
METADATA_DIR = OUT_ROOT / "metadata"
ATLAS_DIR = OUT_ROOT / "atlases"

GROUND_RESOURCE_BASE = 0x4D24 // 4
TERRAIN_DETAIL_BASE = 0x4B04 // 4
TERRAIN_DETAIL_ALT_BASE = 0x4CA4 // 4

SOURCE_BANKS = [
    {
        "id": "ground",
        "source_path": "EMG/NEW_GROUND.EMG",
        "format": "emg_horizontal_runs",
        "expected_group_count": 5127,
        "evidence_level": "confirmed_original",
        "notes": "Terrain base, terrain details, and battle/resource feature sprites.",
    },
    {
        "id": "resource",
        "source_path": "EMG/RESOURCE.EMG",
        "format": "emg_horizontal_runs",
        "expected_group_count": 43,
        "evidence_level": "confirmed_original",
        "notes": "City-resource tile markers from LandTile +0x17.",
    },
    {
        "id": "make",
        "source_path": "EMG/MAKE.EMG",
        "format": "emg_horizontal_runs",
        "expected_group_count": 321,
        "evidence_level": "confirmed_original",
        "notes": "World-map make/road overlays; roads are drawn from LandTile +0x14/+0x13.",
    },
    {
        "id": "road",
        "source_path": "EMG/ROAD.EMG",
        "format": "emg_horizontal_runs",
        "expected_group_count": 236,
        "evidence_level": "confirmed_original",
        "notes": "Confirmed loaded as ROAD.EMG and used by city view roads; not the world-map road draw path.",
    },
    {
        "id": "city",
        "source_path": "EMG/CITY.EMG",
        "format": "emg_horizontal_runs",
        "expected_group_count": 32,
        "evidence_level": "weak_inference",
        "notes": "Parsed bank; exact world-map city sprite selection is not confirmed.",
    },
]

CANONICAL_LAYERS = [
    {
        "id": "terrain_base.original",
        "canonical_layer": "terrain_base",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/extra/decode_new_map.c",
            "reverse/ghidra_export/render/load_emg_base.c",
        ],
        "source_bank": "ground",
        "source_group_expr": "LandTile+0x04, or LandTile+0x06 for special terrain",
        "tile_field_refs": ["LandTile+0x04", "LandTile+0x06"],
        "draw_order": 100,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -40, "blend": "masked"},
    },
    {
        "id": "terrain_detail.original",
        "canonical_layer": "terrain_detail",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": ["reverse/ghidra_export/extra/decode_new_map.c"],
        "source_bank": "ground",
        "source_group_expr": f"{TERRAIN_DETAIL_BASE} + detail_id, or {TERRAIN_DETAIL_ALT_BASE} + detail_id",
        "tile_field_refs": ["LandTile+0x08..0x0e"],
        "draw_order": 200,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -40, "blend": "masked"},
    },
    {
        "id": "resources.battle_feature.original",
        "canonical_layer": "resources",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/extra/decode_new_map.c",
            "remake-workbench/scripts/check_sprite_assets.py",
        ],
        "source_bank": "ground",
        "source_group_expr": f"{GROUND_RESOURCE_BASE} + LandTile+0x16",
        "tile_field_refs": ["LandTile+0x16"],
        "draw_order": 300,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -48, "blend": "masked"},
    },
    {
        "id": "resources.city_resource.original",
        "canonical_layer": "resources",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/render/load_emg_base.c",
            "remake-workbench/scripts/check_sprite_assets.py",
        ],
        "source_bank": "resource",
        "source_group_expr": "LandTile+0x17",
        "tile_field_refs": ["LandTile+0x17"],
        "draw_order": 310,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -58, "blend": "masked"},
    },
    {
        "id": "roads.connection_field.original",
        "canonical_layer": "roads",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/extra/decode_road.c",
            "reverse/ghidra_export/extra/decode_new_map.c",
            "Save/save.MAP",
        ],
        "source_group_expr": "Decode_Road recomputes LandTile+0x13 from adjacent roads and bridges",
        "tile_field_refs": ["LandTile+0x13", "LandTile+0x14"],
        "draw_order": 400,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "blend": "data_only"},
        "notes": "Save/save.MAP validates connection values 0..40 against a Python Decode_Road port.",
    },
    {
        "id": "roads.make_emg_world.original",
        "canonical_layer": "roads",
        "evidence_level": "confirmed_original",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/render/load_emg_base.c",
            "reverse/ghidra_export/all_functions/0x004a3ce0_FUN_004a3ce0.c",
        ],
        "source_bank": "make",
        "source_group_expr": "LandTile+0x14 * 0x51 + LandTile+0x13",
        "tile_field_refs": ["LandTile+0x13", "LandTile+0x14"],
        "draw_order": 405,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": "height_adjusted", "blend": "masked"},
        "notes": "Large-map draw path calls DAT_0075856c/MAKE.EMG at (road_kind * 0x51 + road_id).",
    },
    {
        "id": "roads.bridge_probe",
        "canonical_layer": "roads",
        "evidence_level": "confirmed_original",
        "status": "probe",
        "source_refs": [
            "reverse/ghidra_export/all_functions/0x004a3ce0_FUN_004a3ce0.c",
            "reverse/ghidra_export/extra/decode_road.c",
        ],
        "source_bank": "make",
        "source_group_expr": "0x3cc / 4 + LandTile+0x15",
        "tile_field_refs": ["LandTile+0x15"],
        "draw_order": 410,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -40, "blend": "masked"},
        "notes": "Large-map draw path uses DAT_0075856c/MAKE.EMG at byte offset 0x3cc plus LandTile+0x15 * 4.",
    },
    {
        "id": "roads.long_wall_probe",
        "canonical_layer": "roads",
        "evidence_level": "strong_inference",
        "status": "probe",
        "source_refs": ["reverse/ghidra_export/extra/decode_long_wall.c"],
        "source_bank": "road",
        "source_group_expr": "214 + LandTile+0x24",
        "tile_field_refs": ["LandTile+0x24"],
        "draw_order": 420,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": 0, "pivot_y": -45, "blend": "masked"},
        "notes": "No long-wall-positive sample yet.",
    },
    {
        "id": "cities.save_tail.city_emg_world",
        "canonical_layer": "cities",
        "evidence_level": "strong_inference",
        "status": "active",
        "source_refs": [
            "reverse/ghidra_export/game/load_dat.c",
            "reverse/ghidra_export/game/city_size_scale.c",
            "reverse/ghidra_export/render/load_emg_base.c",
        ],
        "source_bank": "city",
        "source_group_expr": "City population -> City+0x21 level -> CITY.EMG level 0..7; style block unresolved",
        "record_refs": [
            "CountryState+0x1aa city count in Load_Dat city phase",
            "City_0x200+0x16/+0x18",
            "City_0x200+0x21",
        ],
        "draw_order": 500,
        "draw": {"tile_step_x": 48, "tile_step_y": 24, "pivot_x": -18, "pivot_y": -104, "blend": "masked"},
        "notes": "Uses real save-tail city records and CITY.EMG sprites. Population-to-level is confirmed; exact culture/style block selection remains unresolved and currently uses block 0.",
    },
]


def resolve_workspace_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return ROOT / path


def file_sha256(path):
    return hashlib.sha256(resolve_workspace_path(path).read_bytes()).hexdigest()


def load_bank(bank_id):
    bank = next(item for item in SOURCE_BANKS if item["id"] == bank_id)
    return emg_sprites.parse_emg(bank["source_path"])


def build_manifest():
    banks = []
    for bank in SOURCE_BANKS:
        parsed = emg_sprites.parse_emg(bank["source_path"])
        if parsed["group_count"] != bank["expected_group_count"]:
            raise ValueError(
                f"{bank['source_path']} group count {parsed['group_count']} "
                f"!= {bank['expected_group_count']}"
            )
        banks.append({
            "id": bank["id"],
            "source_path": bank["source_path"],
            "format": bank["format"],
            "group_count": parsed["group_count"],
            "sha256": file_sha256(bank["source_path"]),
            "evidence_level": bank["evidence_level"],
            "notes": bank["notes"],
        })
    return {
        "schema_version": 1,
        "generated_from": {
            "workspace_root": str(ROOT).replace("\\", "/"),
            "tool": "remake-workbench/scripts/export_map_resources.py",
            "evidence_policy": "remake-workbench/RESTORATION_BOUNDARIES.md",
        },
        "banks": banks,
        "layers": CANONICAL_LAYERS,
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_manifest(path=None):
    path = Path(path) if path else MANIFEST_DIR / "map_layers.json"
    if not path.is_absolute():
        path = ROOT / path
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_manifest()

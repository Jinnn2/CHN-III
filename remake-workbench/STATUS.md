# Workbench Status

## 2026-06-23

Created the remake workbench and completed the first resource inventory pass.

Command:

```powershell
python remake-workbench\scripts\inventory.py
```

Output:

- `remake-workbench/output/resource_inventory.json`

Initial findings:

- Source resource inventory contains 472 files and 1,126,669,271 bytes.
- Largest resource families are `.img`, `.wav`, `.emg`, and `.xmg`.
- PCX/TMG parsing works for all 15 detected `.pcx`/`.tmg` resources.
- Current `GRAPH/*.TMG` files report as `1280x1024`; this reflects the current
  workspace state and supersedes older notes that listed these backgrounds as
  `1024x768`.
- EMG-like parsing succeeds for 100 of 151 `.emg`/`.xmg` files.
- The unparsed group is mostly `IMAGE/*.XMG`, plus `EMG/NEW_GROUND.EMG`; these
  need the next resource-format pass.

Immediate next work:

1. Add a dedicated XMG parser branch for the unparsed `IMAGE/*.XMG` files.
2. Add DAT/save header probing so map and scenario records can be identified
   before full loading is implemented.
3. Create typed schema stubs for the records listed in `PLAN.md`.
4. Build a tiny read-only map/model loader once DAT block boundaries are
   verified.

Second pass:

- Added XMG high-bit frame parsing based on `load_xmg_resource.c` and
  `FUN_004f8c50`; all 50 `.xmg` files now parse.
- Added MGI scenario-info probing and aligned `MapScenarioInfo_0x16c` offsets
  with `STRUCTURE_NOTES.md`.
- Added gzip MAP probing and MAP/MGI model boundary inference.
- Added `remake-workbench/output/resource_inventory_summary.json`.
- MAP model count is 11/11. Static table prefix is `0x3522c`; LandTile data
  starts there and uses `width * height * 0x100` bytes.
- Template maps have a stable post-land tail of 132,464 bytes. The live
  `Save/SAVE00/SAVE.MAP` tail is 12,066,488 bytes, as expected for a populated
  save with additional runtime records.
- Remaining parser gap: `EMG/NEW_GROUND.EMG` does not match the current
  EMG/XMG group parser and needs a dedicated terrain/ground-format pass.
- Added `scripts/map_inspect.py`, a read-only MAP/MGI inspector with tile
  coordinate helpers and LandTile field sampling.
- Verified `Save/WORLD_FLAT.MAP` and `Save/SAVE00/SAVE.MAP`; the populated save
  reports year 1595, 20/38 countries, and live ownership/resource fields in
  sampled tiles.

Next immediate work:

1. Split the map inspection code into reusable loader/model modules once the
   runtime language is chosen.
2. Add automated checks for map-size modes 0..3 and horizontal wrapping.
3. Start terrain rendering experiments from LandTile sprite ids and GRAPH/EMG
   assets.

Third pass:

- Split reusable MAP/MGI/LandTile loading into `scripts/map_model.py`.
- Converted `inventory.py` and `map_inspect.py` to use the shared model module.
- Added `scripts/check_map_model.py`; it loads all 11 MAP files, verifies map
  modes 0..3, checks LandTile block boundaries, and exercises horizontal wrap
  plus no-wrap/y-overflow behavior.
- Added `scripts/export_terrain_preview.py`, a dependency-free PNG exporter for
  fast terrain/resource/owner previews.
- Generated and visually checked:
  - `output/previews/Save_WORLD_FLAT_terrain.png`
  - `output/previews/Save_SAVE00_SAVE_all.png`

Current verification:

```powershell
python remake-workbench\scripts\inventory.py
python remake-workbench\scripts\check_map_model.py
python remake-workbench\scripts\map_inspect.py Save\SAVE00\SAVE.MAP --tile 0,0 --tile -1,0 --json
python remake-workbench\scripts\export_terrain_preview.py Save\WORLD_FLAT.MAP --overlay terrain --scale 2
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --overlay all --scale 4
```

Next immediate work:

1. Decode `EMG/NEW_GROUND.EMG` or identify the matching terrain sprite bank.
2. Map LandTile `terrain_sprite_id` values to actual art frames instead of
   color-coded terrain kinds.
3. Turn the preview exporter into an interactive read-only map viewer once the
   sprite-backed path is proven.

Fourth pass:

- Confirmed `Load_EMG_Base` loads `EMG/NEW_GROUND.EMG` into `DAT_00758568`.
- Confirmed the large map renderer indexes base terrain as
  `DAT_00758568 + terrain_sprite_id * 4`, with special terrain using
  `special_terrain_sprite_id` and seasonal offsets.
- Added `scripts/emg_sprites.py` to parse the EMG horizontal-run sprite format:
  `uint16 group_count`, then for each group a segment count and repeated
  `x/y/width/pixels` runs.
- Added `scripts/png_writer.py` and upgraded `scripts/export_terrain_preview.py`
  with `--mode sprite`.
- Added `scripts/check_sprite_assets.py`.
- `EMG/NEW_GROUND.EMG` now parses as 5127 sprite groups with no trailing bytes.
- `inventory.py` now accepts that group count; parse coverage is now
  `.emg: 101 / 101 parsed`.
- Generated and visually checked true sprite-backed terrain renders:
  - `output/previews/world_flat_sprite_probe.png`
  - `output/previews/save00_sprite_probe.png`
  - `output/previews/Save_SAVE00_SAVE_sprite_full.png`

Current verification:

```powershell
python remake-workbench\scripts\inventory.py
python remake-workbench\scripts\check_map_model.py
python remake-workbench\scripts\check_sprite_assets.py
python remake-workbench\scripts\export_terrain_preview.py Save\WORLD_FLAT.MAP --mode sprite --viewport 120,120,32,24 --out remake-workbench\output\previews\world_flat_sprite_probe.png
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --out remake-workbench\output\previews\Save_SAVE00_SAVE_sprite_full.png
```

Fifth pass:

- Added `terrain_detail_mode`, `terrain_detail_sprite_ids`, and
  `terrain_layer_or_special_flag` to `map_model.tile_summary`.
- Confirmed the map renderer draws terrain detail from `NEW_GROUND.EMG` pointer
  table offsets `0x4b04` and `0x4ca4`, i.e. group bases `4801` and `4905`.
- Upgraded `scripts/export_terrain_preview.py` to draw LandTile detail overlays
  from `+0x08..0x0e`; `--no-details` keeps a base-terrain comparison path.
- Extended `scripts/check_sprite_assets.py` to scan all MAP files and validate
  detail overlay sprite ids.
- Detail overlay scan covered 113,571 draw calls; highest resolved group id is
  4936, within the 5127 parsed `NEW_GROUND.EMG` groups.
- Generated and visually checked:
  - `output/previews/save00_sprite_details_probe.png`
  - `output/previews/save00_sprite_no_details_probe.png`
  - `output/previews/world_flat_sprite_details_probe.png`
  - `output/previews/Save_SAVE00_SAVE_sprite_details_full.png`

Current verification:

```powershell
python remake-workbench\scripts\check_map_model.py
python remake-workbench\scripts\check_sprite_assets.py
python remake-workbench\scripts\map_inspect.py Save\SAVE00\SAVE.MAP --tile 28,0 --tile 32,0
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --viewport 0,0,40,40 --out remake-workbench\output\previews\save00_sprite_details_probe.png
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --viewport 0,0,40,40 --no-details --out remake-workbench\output\previews\save00_sprite_no_details_probe.png
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --out remake-workbench\output\previews\Save_SAVE00_SAVE_sprite_details_full.png
```

Current limitation:

- Terrain base and detail are now rendered from original art. Resource overlays,
  road/bridge/long-wall overlays, cities, armies, visibility/fog, and precise
  seasonal special-terrain variants remain to be layered.

Next immediate work:

1. Render battle/city resources from `+0x16/+0x17` via `NEW_GROUND.EMG`
   offset `0x4d24` and the static resource tables.
2. Add road/bridge/long-wall overlays from `ROAD.EMG` and terrain fields
   `+0x13..0x15/+0x24`.
3. Identify city and army sprite banks for live save object layers.

Sixth pass:

- Added `ROAD.EMG`, `CITY.EMG`, and `RESOURCE.EMG` parsing checks alongside
  `NEW_GROUND.EMG`.
- Added sprite-backed overlay layer selection to
  `scripts/export_terrain_preview.py`:
  - `--layers resources` draws battle-resource/feature ids from LandTile
    `+0x16` through the `NEW_GROUND.EMG` resource range and city-resource ids
    from LandTile `+0x17` through `RESOURCE.EMG`.
  - `--layers roads` wires LandTile `+0x13/+0x14/+0x15/+0x24` to `ROAD.EMG`
    ranges for roads, bridges, and long-wall candidates.
  - `--layers cities` reserves a `CITY.EMG` marker path for LandTile-linked
    city/object pointers.
- Fixed `scripts/check_sprite_assets.py` so map scans resolve from the project
  root instead of the current working directory.
- Extended `map_model.tile_summary` and `map_inspect.py` with linked
  city/object pointers at `+0x88/+0x8c` plus road/bridge/wall fields.
- Generated and visually checked:
  - `output/previews/save00_sprite_layers_probe.png`

Current verification:

```powershell
python remake-workbench\scripts\check_sprite_assets.py
python remake-workbench\scripts\map_inspect.py Save\SAVE00\SAVE.MAP --tile 0,0 --tile 28,0 --tile 32,0
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --layers all --viewport 0,0,40,40 --out remake-workbench\output\previews\save00_sprite_layers_probe.png
```

Current findings:

- `NEW_GROUND.EMG`: 5127 groups; terrain detail scan covers 113,571 draw calls.
- `ROAD.EMG`: 236 groups; `CITY.EMG`: 32 groups; `RESOURCE.EMG`: 43 groups.
- Resource layer scan across MAP files finds 41,595 battle-resource draws and
  4,455 city-resource draws.
- Current MAP files do not persist live `+0x88` city pointers or road/bridge/
  long-wall connection ids in the LandTile block. `Load_Dat` reconstructs city
  pointers from city records (`City +0x16/+0x18`) after the LandTile block is
  loaded, so the next city layer must parse the populated save tail instead of
  relying on raw LandTile pointer bytes.

Next immediate work:

1. Decode the live save tail order around country states and `City_0x200`
   records so city positions can be overlaid from real city data.
2. Locate a scenario/save with constructed roads or create a controlled editor
   sample, then validate the `ROAD.EMG` road/bridge/long-wall ranges visually.
3. Start army layer probing from the `ArmyUnit_0x164_plus` tail records and
   `ARMY.IMG`/related banks.

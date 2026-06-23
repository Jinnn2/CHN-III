# China2 Modern Remake Workbench

This directory is the new remake workspace. It is intentionally separate from
the executable patching work and from any previous prototype directories.

Goals:

- Keep the original game executable as a behavior reference.
- Convert original resources and fixed-width data tables into typed modern
  assets.
- Manage map resources through the canonical manifest/atlas pipeline in
  `MAP_RESOURCE_PIPELINE.md`.
- Rebuild game rules as a deterministic simulation core.
- Put rendering, input, UI, and tooling around that core without copying the
  old DirectDraw architecture.

Start here:

- `RESTORATION_BOUNDARIES.md`: what is original-compatible, a probe, or remake
  design.
- `MAP_RESOURCE_PIPELINE.md`: the modern map resource scheme for future
  organization and rendering.

```powershell
python remake-workbench\scripts\inventory.py
```

The inventory output is written to `remake-workbench/output/resource_inventory.json`.
The smaller map/resource overview is written to
`remake-workbench/output/resource_inventory_summary.json`.

Inspect a map boundary and a few LandTile records:

```powershell
python remake-workbench\scripts\map_inspect.py Save\WORLD_FLAT.MAP
python remake-workbench\scripts\map_inspect.py Save\SAVE00\SAVE.MAP --tile 0,0 --tile 39,50
```

Run the no-dependency map model checks:

```powershell
python remake-workbench\scripts\check_map_model.py
```

Export a quick PNG terrain preview:

```powershell
python remake-workbench\scripts\export_terrain_preview.py Save\WORLD_FLAT.MAP --mode color --overlay terrain --scale 2
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode color --overlay all --scale 4
```

Export a sprite-backed terrain render using original `NEW_GROUND.EMG` art:

```powershell
python remake-workbench\scripts\export_map_resources.py
python remake-workbench\scripts\check_sprite_assets.py
python remake-workbench\scripts\export_terrain_preview.py Save\WORLD_FLAT.MAP --mode sprite --viewport 120,120,32,24
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --out remake-workbench\output\previews\Save_SAVE00_SAVE_sprite_details_full.png
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --no-details --out remake-workbench\output\previews\Save_SAVE00_SAVE_sprite_base_only.png
python remake-workbench\scripts\export_terrain_preview.py Save\SAVE00\SAVE.MAP --mode sprite --layers all --viewport 0,0,40,40
```

The modern map resource pipeline writes manifests, frame metadata, and preview
atlases under `remake-workbench/output/map_resources/`. City markers in
`--layers cities` are currently modern owner-colored markers driven by real
save-tail `City_0x200` coordinates. Road connection data is validated with
`inspect_road_sample.py`; world-map road visuals are still a probe, exposed as
`--layers road_probe`.

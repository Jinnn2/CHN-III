# China2 Modern Remake Workbench

This directory is the new remake workspace. It is intentionally separate from
the executable patching work and from any previous prototype directories.

Goals:

- Keep the original game executable as a behavior reference.
- Convert original resources and fixed-width data tables into typed modern
  assets.
- Rebuild game rules as a deterministic simulation core.
- Put rendering, input, UI, and tooling around that core without copying the
  old DirectDraw architecture.

Start here:

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

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

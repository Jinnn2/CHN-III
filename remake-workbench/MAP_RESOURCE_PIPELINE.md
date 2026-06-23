# Modern Map Resource Pipeline

This document sets the modern resource-management scheme for all map-related
work after the terrain/resource/road/city probing phase.

The original files remain the source of truth. The remake should not render
directly from scattered hard-coded EMG offsets once a layer is understood.
Instead, map resources move through a stable pipeline:

1. `source`
   - Original assets and records: `.MAP`, `.MGI`, `.EMG`, `.XMG`, `.TMG`,
     `.IMG`, `.DAT`, and save-tail records.
   - Reverse references under `reverse/ghidra_export`.
   - Binary hashes and parse evidence are preserved.

2. `canonical`
   - Typed map model and layer manifests.
   - Original ids, offsets, record sizes, and evidence levels are kept.
   - No renderer-specific coordinates except original draw pivots and
     z-order hints recovered from the executable.

3. `atlas`
   - Converted bitmap pages plus frame metadata.
   - Multiple original banks can be merged into a single modern atlas, but
     every frame keeps its `source_bank`, `source_group`, and hash lineage.

4. `render_graph`
   - Declarative layer order for terrain, details, resources, roads, cities,
     armies, fog, markers, and editor overlays.
   - Each draw command references canonical layer entries, not raw file
     offsets.

5. `runtime`
   - The game consumes canonical records and atlas ids.
   - Modern renderer can choose resolution, batching, culling, animation, and
     UI style without changing restored data semantics.

## Directory Layout

Use this layout for generated map resources once exporters are added:

```text
remake-workbench/
  output/
    map_resources/
      manifests/
        map_layers.json
        source_banks.json
      atlases/
        map_terrain.png
        map_objects.png
        map_ui_markers.png
      metadata/
        map_terrain.frames.json
        map_objects.frames.json
        layer_draw_rules.json
      diagnostics/
        source_hashes.json
        unresolved_original_fields.json
```

Generated files should be reproducible from original resources and scripts.
Do not hand-edit generated atlas metadata; update the exporter or the manifest
source instead.

## Canonical Layer Model

All map rendering should target these canonical layers:

- `terrain_base`
  - Confirmed original.
  - LandTile `+0x04/+0x06` through `EMG/NEW_GROUND.EMG`.

- `terrain_detail`
  - Confirmed original.
  - LandTile `+0x08..0x0e`, bases `4801` and `4905` in
    `EMG/NEW_GROUND.EMG`.

- `resources`
  - Confirmed for field presence and current sprite ranges.
  - LandTile `+0x16` uses `EMG/NEW_GROUND.EMG` resource range.
  - LandTile `+0x17` uses `EMG/RESOURCE.EMG`.

- `roads`
  - Basic road connection data is confirmed original from `Save/save.MAP`.
  - `Decode_Road` recomputes LandTile `+0x13` from adjacent roads and bridges;
    the large-map renderer draws that field through `EMG/MAKE.EMG` as
    `LandTile+0x14 * 0x51 + LandTile+0x13`.
  - `ROAD.EMG` is proven for city-view roads in `put_city_view.c`; it is not
    the confirmed large-map road bank.
  - Bridge `+0x15` is confirmed in the large-map draw path as
    `MAKE.EMG[0x3cc / 4 + LandTile+0x15]`.
  - Long-wall mapping from `+0x24` remains a probe until sample-backed.

- `cities`
  - Partially restored original rendering.
  - Raw MAP LandTile `+0x88/+0x8c` does not persist live city pointers.
    City positions must come from save-tail `City_0x200` records rebuilt by
    the `Load_Dat` order.
  - `CITY.EMG` is the active sprite bank; `City_Size_Scale` confirms the
    population-to-`City+0x21` level mapping. Exact culture/style block
    selection in `CITY.EMG` remains unresolved and currently uses block 0.

- `armies`
  - Pending original restoration.
  - Army positions should come from validated `ArmyUnit_0x164_plus` records
    and reconstructed tile occupancy, not visual guesswork.

- `fog_visibility`
  - Pending original restoration or explicit remake design.
  - Keep per-country visibility data separate from presentation choices.

- `editor_markers`
  - Remake tooling layer.
  - May use modern symbols and colors, but must not be confused with original
    game rendering.

## Manifest Rules

Every canonical layer entry must include:

- `id`: stable modern identifier.
- `layer`: canonical layer name.
- `evidence_level`: one of the values in `RESTORATION_BOUNDARIES.md`.
- `source_refs`: original file, record, reverse file, or offset evidence.
- `source_bank`: original sprite bank when visual art is used.
- `source_group_expr`: exact original group id or expression when known.
- `draw`: pivot, y-adjust, z-order, blend, and animation hints.
- `status`: `active`, `probe`, `blocked`, or `remake_design`.

Weak or blocked entries may exist in manifests only when their status makes the
uncertainty explicit. Runtime gameplay should ignore weak probes unless a
debug/tooling mode requests them.

## Rendering Policy

The modern renderer may:

- Pack sprites into larger atlases.
- Use GPU batching and camera culling.
- Add high-DPI scaling and smooth camera movement.
- Add debug overlays, selection outlines, and editor handles.

The modern renderer must not:

- Change original tile ids or inferred records to make drawing easier.
- Hide unresolved original-restoration gaps behind remake art.
- Treat road/city/army probes as confirmed behavior before validation.

## Exporter Migration Path

Current scripts can keep their direct EMG constants while evidence is being
gathered. New work should migrate in this order:

1. Emit source bank metadata for `NEW_GROUND.EMG`, `MAKE.EMG`,
   `RESOURCE.EMG`, `ROAD.EMG`, and `CITY.EMG`. Done in
   `scripts/export_map_resources.py`.
2. Emit a canonical `map_layers.json` from the confirmed terrain/detail/resource
   rules. Done.
3. Change preview rendering to read layer rules from the manifest. Started.
4. Add city records from save-tail parsing as a canonical `cities` source. Done
   for `Save/SAVE00/SAVE.MAP` and `Save/SAVE01/SAVE.MAP` using `Load_Dat`
   city-section order; `CITY.EMG` sprite level is restored from population,
   while exact style block selection remains pending.
5. Add roads only after positive original evidence validates both connection
   data and visual draw path. Done for `+0x13/+0x14` roads via `MAKE.EMG`;
   bridge `+0x15` is also confirmed via `MAKE.EMG`; long-wall samples remain
   needed.
6. Add armies after live unit records and tile occupancy are confirmed.

## Decision Boundary

If original restoration stalls, record the gap in
`RESTORATION_BOUNDARIES.md` and ask for a remake-design decision before
building a replacement system. Modern resource management is approved here;
modernized gameplay semantics are not implied by this document.

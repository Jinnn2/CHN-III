# Modern Remake Implementation Plan

## Position

The remake should be data-compatible first, visually modern second. The reverse
engineering under `reverse/ghidra_export` has already recovered enough structure
to avoid a blind rewrite:

- `Load_Dat` defines the data loading order and record sizes.
- `Do_City`, `City_Resource_Change`, and `City_Building` define the first major
  deterministic simulation target.
- `Order_Go`, `AI_Army`, and related order queue functions define movement and
  AI behavior.
- `Map_To_Battle_Army`, `Make_Battle_Map`, and
  `Do_Battle_Army_And_Battle_Die` define the battle simulator.
- `.TMG`, `.EMG`, `.XMG`, `.IMG`, and `.IDI` resources should be converted into
  modern atlas and metadata assets.

## Architecture

Use four layers:

1. Resource conversion
   - Read original binary resources.
   - Emit PNG/atlas/JSON where possible.
   - Keep hashes, sizes, parse status, and source paths for traceability.

2. Data model
   - Recreate fixed records as typed structures.
   - Preserve original ids and enum values.
   - Load original maps and saves into the modern model.

3. Rule core
   - Deterministic, headless, testable simulation.
   - No rendering or input dependencies.
   - Systems: city, production, research, map, movement, order queue, AI,
     diplomacy, battle.

4. Presentation
   - Modern renderer and UI.
   - Original 4:3 layout mode for behavior verification.
   - High-resolution 16:9 UI after core behavior is stable.

## Milestones

### M0: Inventory And Evidence

- Build an inventory of source resources and table assumptions.
- Parse PCX/TMG dimensions.
- Parse EMG group/frame summaries.
- Record DAT file sizes and inferred table dimensions.
- Output machine-readable JSON.

Done when `scripts/inventory.py` produces a useful inventory without modifying
game files.

### M1: Read-Only Map Viewer

- Load map dimensions from scenario/save data.
- Display terrain, resource ids, cities, and army positions.
- Implement tile coordinate conversion and wrapping.

Done when a real map can be inspected in a modern window.

### M2: City Turn Simulator

- Port the `Do_City` call sequence.
- Implement city resource, worker, event, and production calculations.
- Create golden tests from original saves.

Done when selected city fields match original behavior for several turns.

### M3: Unit Movement And Orders

- Implement order queue state.
- Port movement/path stepping from `Order_Go` and `TestRoad`.
- Repair tile occupant lists from loaded units.

Done when units can move across a loaded map and update tile occupancy.

### M4: Production, Research, And Economy

- Finish building/special project completion.
- Implement science progress and unlock propagation.
- Implement government and building modifiers.

Done when country-level economy and science outputs match golden samples.

### M5: Battle Simulator

- Implement 24x24 battle grid.
- Convert map units into battle units.
- Run attack, movement, death, and outcome resolution as event streams.

Done when a seeded battle resolves reproducibly and can be visualized.

### M6: Playable Vertical Slice

- One real scenario.
- City management.
- Unit movement.
- End turn.
- One battle path.

Done when the remake is playable for a short, constrained session.

## Immediate Work Queue

1. Create resource inventory. Done.
2. Add source-resource parsers for TMG/PCX, EMG, XMG, MGI, and MAP. Done for
   summaries/probes; full pixel/audio conversion remains later work.
3. Build table schema stubs from recovered record sizes. Started in
   `schemas/core_records.json`.
4. Implement map coordinate helpers and tests.
5. Build a read-only map model loader from the MAP/MGI boundaries now recorded
   in `output/resource_inventory_summary.json`.
6. Choose core language/runtime after the first map loader proves the data
   boundary.

## Known Risks

- Several fields in `UNCERTAINTIES.md` need UI text and save-diff correlation.
- Some EMG/XMG/IMG payload details are still only partially understood.
- The original game mixes rule changes, UI notifications, and animation state in
  the same functions; the remake must split those carefully.
- Randomness and frame-budgeted processing need explicit deterministic handling.

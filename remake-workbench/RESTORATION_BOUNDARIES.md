# Restoration Boundaries

This workbench separates original restoration from remake design.

## Evidence Levels

- `confirmed_original`: directly supported by reverse output plus matching
  resource/save data. These can be implemented as original-compatible behavior.
- `strong_inference`: multiple original-code clues agree, but a final sample or
  golden check is still missing. These can live in tools as probes, with the
  uncertainty named.
- `weak_inference`: plausible but not yet proven. These should not become core
  behavior without a decision.
- `remake_design`: difficult or not worthwhile to recover exactly. These need a
  separate design decision before implementation.

## Current Original-Compatible Areas

- MAP/MGI dimensions, map size modes, horizontal wrapping, and LandTile block
  boundaries.
- LandTile terrain base sprites from `EMG/NEW_GROUND.EMG`.
- Terrain detail overlays from LandTile `+0x08..0x0e` using `NEW_GROUND.EMG`
  bases `0x4b04 / 4` and `0x4ca4 / 4`.
- Battle/city resource tile markers from LandTile `+0x16/+0x17`, with resource
  art currently validated against `NEW_GROUND.EMG` and `RESOURCE.EMG`.
- Static resource formats for TMG/PCX, EMG, XMG, MGI, and gzip MAP boundaries.

## Pending Original Restoration

- Live city layer: `Load_Dat` rebuilds LandTile `+0x88/+0x8c` city pointers
  from `City_0x200` records after loading. The raw MAP LandTile block does not
  persist these pointers, so city overlay must parse the populated save tail.
- Road connection field: basic roads are now confirmed from the controlled
  `Save/save.MAP` sample. `Decode_Road`/`Decode_NewMap` recompute LandTile
  `+0x13` from adjacent roads and bridges, and the Python port matches the
  sample values.
- Road visual layer: not confirmed. `ROAD.EMG` is loaded and is proven in
  `put_city_view.c` for the 48x48 city-view road layer, but current reverse
  evidence does not prove that `ROAD.EMG` is used for world-map roads.
- Bridge/long-wall layer: LandTile fields `+0x15/+0x24` are wired as probes,
  but current samples do not contain positive bridge or long-wall ids.
  Controlled samples are still needed before treating those visual ranges as
  confirmed.
- Army layer: `Load_Dat` shows `ArmyUnit_0x164_plus` records after the city
  phase, but the exact live tail boundary still needs confirmation before
  drawing units from original data.

## Likely Remake-Design Decisions

These should be discussed before implementation if original recovery stalls:

- Modern city visual style if original city object placement cannot be fully
  recovered from `City_0x200` and city-map records.
- Road network semantics if no original save/editor sample with built roads can
  be produced.
- Fog/visibility presentation if the original per-country visibility bytes are
  too coupled to UI state for a clean modern renderer.
- Army animation and selection UI after static unit positions are recovered.

## Working Rule

No weak inference should be promoted into the simulation core or canonical
asset model. Weak probes may exist in scripts if they are named as probes and
document what evidence is still missing.

Map resource modernization is approved at the organization/rendering boundary:
original assets and records feed the canonical manifest/atlas pipeline described
in `MAP_RESOURCE_PIPELINE.md`. This does not approve changing unresolved
original gameplay semantics without a separate design decision.

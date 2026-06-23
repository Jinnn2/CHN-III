# DAT / Save Loader Function Notes

This note is the current navigation point for the DAT/save parser. It focuses
on parse phases, globals touched, and follow-up entry points instead of keeping
more raw decompiler output.

## Function 0x00473270 - Load_Dat

### Status

partial

### Inputs

- `param_1`: map/save base name or path fragment used to build the compressed
  DAT path.
- `param_2`: sidecar/place-name base name; reused when named-point files are
  present.
- `param_3`: load mode flag. `0` reads scenario info and empire definitions;
  nonzero mode skips/appends over some definition blocks while still advancing
  the memory stream.

### Globals Read

- `g_map_data_dir`
- `g_current_map_scenario_info`
- `g_scripted_start_mode_enabled`
- `g_building_defs`, `g_city_resource_defs`, `g_army_type_table` during
  validation and derived-field rebuilds.
- `g_country_states` while iterating country-owned city, army, and business
  sections.

### Globals Written

- Static definition tables: `g_science_defs`, `g_army_type_table`,
  `g_building_defs`, `g_country_profile_defs`, `g_government_defs`,
  `g_ground_defs`, `g_city_resource_defs`, flag image blocks.
- Map state: `g_map_size_mode`, `g_map_width_tiles`, `g_map_height_tiles`,
  `g_land_tiles`, view-center globals, `g_land_record_buffers`.
- Scenario/country state: `g_empire_country_defs`, `g_country_states`,
  `g_human_country_index`, current active-country pointer setup.
- Dynamic lists: city list, army list, death-object list, business/trade list.
- Named-point tables: `g_secondary_named_points`, `g_primary_named_points`, and
  the named-point indices inside land tiles.
- Minimap and post-load runtime caches.

### Calls

- `0x004fc230` `Gzip_GetSize_Or_Decompress_candidate`
- `Clear_All_Memory`
- `Clear_UnUsed_Science`
- `FUN_0047de30` / `FUN_0047de70` allocation/free wrappers.
- `FUN_00471fb0` city list insert/init candidate.
- `FUN_00471bf0` army list insert/init candidate.
- `FUN_00471f10` death-object list insert/init candidate.
- `FUN_00472630` business/trade list insert/init candidate.
- `City_Army_Error_Fix`
- `Decode_MiniMap`
- `CloseIndexIMG`, `Safe_LoadIMG`/indexed portrait loader family.

### Container and Memory Stream

- The loader first reads a small direct header/check area, then validates a
  version/build value using `DAT_00707928 + DAT_00707924 * 100 < 0x13e`.
- The compressed payload is handled through `0x004fc230`: call with
  `param_2 == 0` returns the expected uncompressed size; call with
  `param_2 != 0` decompresses into `Load_Dat: MemBuf`.
- `DAT_00707920` is a moving memory-stream cursor. The original buffer base is
  kept separately on the stack and freed later as `Load_Dat: MemStart`.
- `DAT_0070792c` tracks consumed bytes/progress. It is used for loading-bar
  updates and should be treated as an offset, not a typed table pointer.

### Static Definition Section

Parse order after decompression:

1. `g_science_defs`: `0x6a40` bytes, likely 200 records of `0x88`.
2. `g_army_type_table`: `0x16c00` bytes, 91 records of `0x400`; then derives
   `build_cost_digit_count`.
3. `g_building_defs`: `0xc000` bytes. Existing code uses `0x200` stride, but
   table count needs verification before renaming the whole array.
4. `g_country_profile_defs`: `0x3070` bytes, 100 records of `0x7c`.
5. `g_government_defs`: `0x3a0` bytes, 8 records of `0x74`.
6. `g_ground_defs`: `0x21c` bytes, 15 records of `0x24`.
7. `g_city_resource_defs`: `0x21c0` bytes, 40 records of `0xd8`.
8. Flag image blocks: 100 blocks of `0x100`.

### Map and Country Section

- `g_current_map_scenario_info.map_size_mode` selects dimensions:
  - mode `0`: `0x138` by `0x192`
  - mode `1`: `0x9c` by `0xc9`
  - mode `2`: `0x4e` by `100`
  - mode `3`: `0x27` by `0x32`
- Land tiles are copied as `tile_count * 0x100` bytes into `g_land_tiles`.
  Runtime occupant/pointer slots are then cleared or rebuilt.
- The loader reads view-center x/y, then `DAT_00755248`, used as the per-country
  land-record buffer length.
- `g_empire_country_defs` is copied only in `param_3 == 0` mode; otherwise the
  stream still advances over the same `0xc800` bytes.
- `g_country_states` is copied as `0x13cf0` bytes. This equals 22 records of
  `0xe68`; some other docs still reserve 24 slots, so keep the distinction
  explicit until all callers are reconciled.
- Per-country land-record buffers are allocated for active countries and sized
  as `DAT_00755248 * 4`.

### City Section

- Reads a 5-byte section marker, then `DAT_0074cf24` as expected city total.
- For each active country, the city count comes from `CountryState +0x1aa`.
- Each city record is allocated as `0x200` bytes with tag `Load_Dat: City`.
- If the city-map flag is enabled, an extra `0x12000` bytes are read and stored
  from tag `Load_Dat: City_Map`.
- Runtime pointer bytes around `+0x1b0..+0x1bf` are cleared after file data is
  read.
- `FUN_00471fb0` links/inits the city; the owning land tile receives the city
  pointer in slots `+0x88/+0x8c` as decompiler dword slots `0x22/0x23`.
- The city path also refreshes local resource availability against
  `g_city_resource_defs`.

### Army Section

- Reads a 5-byte section marker, then `DAT_0074d518` as expected army total.
- For each active country, the army count comes from `CountryState +0x7c`.
- Each army/subunit record is `0x200` bytes with tag `Load_Dat: Army`.
- After each record, two extra integers are read as city coordinates used to
  resolve `stationed_city` from the land tile city pointer.
- `FUN_00471bf0` links/inits the army.
- Primary tile occupant slots are rebuilt at land-tile dword slot
  `0x0a + battle_slot_or_category`.
- Moving/mission armies can also populate the secondary/arrival slots around
  dword slot `0x15 + field_0x19`.
- Cached stats are rebuilt from `g_army_type_table`, including movement scaled
  by `g_current_map_scenario_info.movement_base`.
- Nested cargo/subunit records are loaded with the same `0x200` record shape.

### Death and Business Sections

- Death section reads a 5-byte marker, then `_DAT_0074a1e0` count.
- Each death/object record is `0x20` bytes with tag `Load_Dat: Die`; the last
  two dwords are cleared before `FUN_00471f10` links the record.
- Death/object pointer is written back to land-tile dword slot `0x24`.
- Business/trade section reads a 5-byte marker, then `DAT_0075524c` total.
- Each business record reads four coordinate/id integers, then a `0x100`-byte
  payload tagged `Load_Dat: Business`.
- The source/destination city pointers are resolved from land tiles and stored
  in record dwords `[1]` and `[2]`.
- `FUN_00472630` links valid same-owner records; mismatched duplicates can be
  freed instead of linked.

### Finalization and Sidecars

- Reads `0x50` bytes into the map-bookmark slot block starting at `0x005c7810`.
- Frees the decompressed buffer, clears `DAT_00707920`, calls
  `City_Army_Error_Fix`, and rebuilds every minimap tile through
  `Decode_MiniMap`.
- Runs post-load cache/resource refresh helpers, then loads `DIP_%02d.IMG` /
  `.IDI` portrait resources from country profile definitions.
- If `place_name_setting == 1`, sidecar files selected through `param_2` load:
  - `g_secondary_named_points`: `1000 * 0x20`.
  - `g_primary_named_points`: `4500 * 0x20`.
- Named-point names are space-trimmed and land-tile named-point index fields
  are rebuilt. If sidecars are missing or the setting is disabled, the named
  point tables are cleared.

### Confidence

85%

## Function 0x004fc230 - Gzip_GetSize_Or_Decompress_candidate

### Status

partial

### Inputs

- `param_1`: path when querying size; decompiler currently reuses this name as
  the destination pointer in the decompress branch, so the prototype is likely
  wrong.
- `param_2`: mode/destination. `0` means size query, nonzero means decompress.

### Globals Read

- zlib/gzip mode strings around `0x00575af8`.
- Temporary chunk buffer at `0x0077748c`.

### Globals Written

- Caller-supplied output buffer in decompress mode.

### Calls

- `FUN_004fc340`: gzopen-like helper.
- `FUN_004fc7f0`: gzread-like helper.
- `FUN_004fcba0`: gzclose-like helper.
- `FUN_00503f7a`, `FUN_00504a04`, `FUN_00503e72`, `FUN_00503e1c`: stdio-style
  open/seek/read/close helpers for reading the gzip ISIZE trailer.

### Observations

- In size-query mode, opens the file normally, seeks to `-4` from end, reads a
  4-byte little-endian value, and returns it. For gzip streams this matches the
  ISIZE trailer.
- In decompress mode, opens through the gzip helper, reads chunks of `0x1000`
  bytes into `0x0077748c`, copies each chunk to the output buffer, and returns
  total bytes written.
- The function is a container helper, not DAT-specific, but `Load_Dat` is the
  currently proven caller.

### Confidence

75%

## DAT Parser Follow-Up Queue

- Isolate the save/write counterpart by searching for `Load_Dat: MemStart`,
  gzip close/open helpers, or writes of the same section-marker strings.
- Inspect `FUN_00471fb0`, `FUN_00471bf0`, `FUN_00471f10`, and `FUN_00472630`
  as list insertion helpers before naming dynamic list heads more aggressively.
- Reconcile `g_country_states` storage: `Load_Dat` copies 22 `0xe68` records,
  while some globals reserve room for 24.
- Use editor table setup functions to resolve static DAT fields instead of
  guessing from the loader.

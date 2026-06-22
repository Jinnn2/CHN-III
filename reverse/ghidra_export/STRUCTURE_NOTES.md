# Structure Recovery Notes

These notes are inferred from the decompiled output and embedded debug strings.
They are working names, not confirmed original type names.

The first-pass names and structures here are also applied automatically by
`tools/reverse_probe/GhidraSemanticAnnotate.java` before each export. That is
why regenerated pseudocode now contains names such as `Do_City`,
`g_current_city`, `City_0x1b8_plus`, `g_active_country`, `LandTile_0x100`,
`business_workers`, and `g_primary_surface`.

## Core Records

| Working type | Evidence | Likely meaning |
|---|---|---|
| `LandTile_0x100` | `load_dat.c` copies/iterates `DAT_0074a040` in `0x100`-byte strides. | Map tile/cell record. |
| `CountryState_0xe68` | `load_dat.c` copies into `DAT_007350b8`; loops advance by `0xe68`; `do_city.c` uses `DAT_007350b8 + country_index * 0xe68`. | Player/country/faction state. |
| `City_0x1b8_plus` | `do_city.c` iterates `DAT_00706948`; `load_dat.c` links records through offset `+0x1b4`; city x/y at offsets `+0x16/+0x18`; name-like text starts around `+3`. | City record linked list. |
| `BattleUnit_0x64` | `BattleArmy` allocates 100-byte chunks; `Do_Battle_Army_And_Battle_Die`, `Battle_AutoArrange`, and arrange/UI code read typed x/y, state, stat, and linked-list fields. | Battle-side army/unit record. |
| `Image/Sprite bank` | Main menu and UI paths call function pointer `DAT_00771f34` with entries from `DAT_00707f90`, and load `.EMG`/`.XMG` resources. | Decoded sprite/image resources. |
| `BuildingDef_0x200` | Building table starts at `0x005997b8`; UI/editor and city production index it with `building_id * 0x200`. | Per-building definition table. |
| `SpecialProjectDef_0x200` | Special-project table starts at `0x005a19d4`; build queue maps entries `0x8c..0xa4` to project ids. | Wonder/special project definitions. |
| `ScienceDef_0x88` | Science table starts at `0x005817a8`; research code advances by `0x88` bytes and formats names from the record. | Per-science/research definition table. |
| `CountryProfileDef_0x7c` | Static table starts at `0x00596218`; `load_dat.c` reads/writes `0x3070` bytes, i.e. 100 records of `0x7c`; country `+0x03` indexes this table. | Country/civilization profile and modifier table. |
| `ArmyTypeDef_0x400` | `Load_Dat` reads `0x16c00` bytes into `g_army_type_table`, i.e. 91 records of `0x400`; map armies index this table by `army_type_id`. | Static unit/army definitions. |
| `BattleGridCell_0x30` | `Make_Battle_Map` clears `0x6c00` bytes from `g_battle_grid_cells`, i.e. `24 * 24 * 0x30`; battle arrange/update paths address cells by `x + y * 0x18`. | One cell in the 24x24 battle grid. |

## Important Globals

| Address/global | Evidence | Working meaning |
|---|---|---|
| `g_land_tiles` | `load_dat.c`, `do_city.c` tile address arithmetic. | Base pointer for `LandTile_0x100[]`. |
| `g_map_width_tiles` | Map width-like dimension after `load_dat.c` map-size switch. | Map width in tiles. |
| `g_map_height_tiles` | Map height-like dimension after `load_dat.c` map-size switch. | Map height in tiles. |
| `g_country_states` | Country table base, stride `0xe68`. | `CountryState_0xe68[]`. |
| `g_active_country_index` | Used as index into country table in city simulation. | Active country/player index. |
| `g_human_country_index` | Compared against active country; used after load. | Human/current player country index. |
| `g_city_turn_list_head` | City loop head/current pointer in `do_city.c`. | Current city pointer for per-turn processing. |
| `g_current_city` | Current city pointer inside `do_city.c`. | Active `City_0x1b8_plus *`. |
| `g_active_country` | `g_country_states + g_active_country_index * 0xe68`. | Active `CountryState_0xe68 *`. |
| `g_building_defs` | `0x005997b8`, 65 records, `0x200` byte stride. | Static building definitions loaded from table data. |
| `g_special_project_defs` | `0x005a19d4`, 25 records, `0x200` byte stride. | Static special-project definitions. |
| `g_science_defs` | `0x005817a8`, 200 records, `0x88` byte stride. | Static science/research definitions. |
| `g_country_profile_defs` | `0x00596218`, 100 records, `0x7c` byte stride. | Static country profile definitions and modifiers. |
| `g_army_type_table` | `0x005aa2c8`, 91 records, `0x400` byte stride. | Static unit/army definition table. |
| `g_battle_unit_count_by_side` | `Battle_AutoArrange` sizes an 8-byte work array from it; `Map_To_Battle_Army` clears both entries before battle setup. | Battle unit/formation count for side 0/1. |
| `g_battle_unit_list_head_by_side` | `Battle_AutoArrange` and arrange/UI code traverse `BattleUnit_0x64.next_battle_unit` from these heads. | Per-side linked-list heads for battle records. |
| `g_battle_total_units_by_side` | `BattleArmy` increments once per source map army; `Make_Battle_Map` compares class counts against this total. | Source army count by battle side. |
| `g_battle_land_units_by_side` | `BattleArmy` increments it when `ArmyTypeDef.unit_class == 0`; `Make_Battle_Map` checks whether land units exist. | Land-class army count by side. |
| `g_battle_air_or_class1_units_by_side` | `BattleArmy` increments it when `ArmyTypeDef.unit_class == 1`; `Make_Battle_Map` uses it for battle-map selection. | Class-1/air-like army count by side. |
| `g_battle_special_or_class2_units_by_side` | `BattleArmy` increments it for non-0/non-1 unit classes. | Class-2/special army count by side. |
| `g_battle_frontline_land_units_by_side` | `BattleArmy` increments it for land units outside the ranged/support condition. | Frontline land army count by side. |
| `g_battle_ranged_land_units_by_side` | `BattleArmy` increments it for land units with low support value and attack stat above 1. | Ranged/support land army count by side. |
| `g_battle_attacker_land_tile` / `g_battle_defender_land_tile` | Battle start paths assign them as `g_land_tiles + tile_index * 0x100`; `Map_To_Battle_Army`, `Make_Battle_Map`, and battle update read tile occupants/object links through them. | Map tiles that seed the current battle. |
| `g_battle_tile_has_object_by_side` | `Prepare_Battle_Tile_Object_Flags` sets entries from `LandTile.linked_record != NULL`; battle resolution checks this when allowing special class/object interactions. | Per-side tile-object/city-present flags. |
| `g_battle_attacker_slot_present` / `g_battle_defender_slot_present` | `Map_To_Battle_Army` marks `ArmyUnit.battle_slot_or_category` values while collecting units from each tile. | Per-side source army slot/category presence flags. |
| `g_battle_attacker_source_group_count` / `g_battle_defender_source_group_count` | `Map_To_Battle_Army` counts primary army plus cargo/subunits for the attacker and collected defender groups. | Source map-unit group counts before battle records are expanded. |
| `g_battle_grid_cells` | `Make_Battle_Map` clears and fills a `24 * 24` grid in `0x30`-byte strides; `Decode_Battle` derives rendered tile indices from it. | `BattleGridCell_0x30[0x240]`. |
| `g_battle_grid_front_units` / `g_battle_grid_back_units` | Arrange and battle update code place `BattleUnit_0x64 *` at cell offsets `+0x14/+0x1c`. Ghidra renders them as pointer-array aliases with `idx * 0xc` because the real cell stride is `0x30`. | Front/back visible battle-unit slots inside each grid cell. |
| `g_battle_grid_front_aux_units` / `g_battle_grid_back_aux_units` | Battle update stores moving/target unit pointers at cell offsets `+0x18/+0x20`. | Auxiliary front/back battle-unit slots. |
| `g_battle_grid_effect_or_projectile` | `Do_Battle_Stone` and death/update paths store transient effect records at cell offset `+0x24`. | Per-cell effect/projectile pointer slot. |

## Useful Offsets

### `LandTile_0x100`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x02` | `Make_Battle_Map` uses this as a fallback when the primary tile kind is outside `0..10`. | alternate battle terrain kind. |
| `+0x08` | `Map_To_Battle_Army` changes battle stat modifiers when this signed value is positive, especially value `4`. | battle stat terrain mode. |
| `+0x10` | `load_dat.c` checks and counts. | city/land occupancy count or resource count. |
| `+0x12/+0x13` | `city_round_check.c`, `near_beach_city_found.c`, and `no_dpa_near_city_near_sea.c` treat these as signed markers beside `+0x10`. | region / terrain / link markers. |
| `+0x16` | `Map_To_Battle_Army` indexes table `0x00589644` and adds battle stat bonuses when valid. | battle resource or feature id. |
| `+0x24` | `Map_To_Battle_Army` switches between terrain-dependent modifiers and doubled defense/support bonuses based on the sign of this byte. | battle stat bonus mode. |
| `+0x25` | `City_Belong_Change` writes the new city owner here; near-city scans require it to match the active country. | tile owner/controller country id. |
| `+0x27` | `City_Belong_Change` writes the same new owner; `Diplomat_Allow` compares it with source/target ownership pairs. | secondary or previous owner country id. |
| `+0x28` | `load_dat.c` stores pointers indexed by `army_slot * 4`; city/battle scans now type these as `ArmyUnit_0x164_plus *`. | primary army pointer list. |
| `+0x50` | `load_dat.c` checks tile count/list. | army/unit count or city count. |
| `+0x54` | `load_dat.c` stores pointers indexed by slot; `City_Belong_Change` re-owns units from this list after capture. | secondary army pointer list. |
| `+0x7c` | `do_city.c`, `city_building.c`, and `city_people_change.c` add/check it beside the primary occupant count. | secondary occupant/defender count. |
| `+0x88` | `load_dat.c` dereferences during map repair. | linked record pointer or terrain object. |
| `+0xaa` | `City_Round_Check` compares this marker against `'('` while testing nearby tiles. | terrain or resource marker. |
| `+0xb3` | `City_Round_Check` tests this flag before allowing selected nearby-city actions. | city-round block flag. |
| `+0xb5..0xca` | `Diplomat_Allow`, `Do_Map`, `near_city_user_know_found`, and `user_set_city_resource` index by country id. | per-country visible/known flags. |
| `+0xcb..0xe0` | `City_Round_Check` tests `active_country + 0xcb` as a secondary exclusion/visibility gate. | per-country secondary visibility/exclusion flags. |

### `ArmyUnit_0x164_plus`

This is the map-level army/unit record, separate from the smaller battle-unit
records allocated by `BattleArmy`. `Map_To_Battle_Army` now takes this type
directly, while `BattleArmy` consumes it to create battle records.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | `Map_To_Battle_Army` and `BattleArmy` use it as `g_army_type_table` index. | army type id. |
| `+0x01` | `City_Belong_Change` compares/re-owns units when a city changes owner. | owner country id. |
| `+0x02` | `Map_To_Battle_Army` compares it with owner and battle-side country ids. | target or previous owner id. |
| `+0x18` | `Map_To_Battle_Army` indexes battle-side presence arrays. | battle slot/category. |
| `+0x1a/+0x1c` | `Start_Map_Battle_From_Army` and `Start_Map_Battle_From_Tile` combine these with map-width strides to find the source `LandTile`. | map tile x/y. |
| `+0x1e/+0x20` | Battle entry movement paths pass these to animation helpers after `FUN_004d2cc0` schedules movement. | render or animation x/y. |
| `+0x22/+0x24` | Battle entry and near-city pathing code stores computed destination coordinates before calling `FUN_004d2cc0`. | target tile or animation x/y. |
| `+0x120` | Battle entry code tests this after movement/path scheduling before emitting animation records. | active animation step count. |
| `+0x127` | Near-city scans require zero for active/free units; diplomat order code sets it to nonzero. | mission state. |
| `+0x128` | Load/order paths test or write action ids such as `0x35`, `0x36`, `0x37`, and `0x39`. | mission/action id. |
| `+0x129` | Battle entry paths index direction tables `DAT_00589344`, `DAT_00589374`, and `DAT_005893b4` with this value to find the tile ahead. | facing or move direction. |
| `+0x12a` | Battle entry paths accumulate it by the turn/order delta and compare it with `ArmyTypeDef.mission_range_limit`, then reset it on action. | mission progress counter. |
| `+0x12f` | `BattleArmy(..., unit->strength_or_health / 0xe + 1, ...)` derives formation count from it. | strength/health byte. |
| `+0x130` | Battle entry paths increment and reset it around repeated battle-entry/stat checks before raising veteran/power state. | battle entry retry counter. |
| `+0x131` | Battle stat adjustment shifts by this value in `Map_To_Battle_Army`. | veteran level / power shift. |
| `+0x134/+0x136/+0x138` | Loaded from army type tables and cached as short stats. | cached stat shorts. |
| `+0x13c` | `BattleArmy` copies this value into `BattleUnit_0x64.map_unit_extra_id`; death/effect records later reuse it. | map unit extra id. |
| `+0x144` | Direct-unit checks require null; other paths dereference it as another army. | transport parent pointer. |
| `+0x148` | Near-city capacity and battle conversion add one to this value for carried/sub units. | cargo/subunit count. |
| `+0x14c` | Cargo/subunit scans compare this pointer against the current unit. | transport or carrier link. |
| `+0x152` | Battle entry and tile scans require zero for directly present active units; startup/battle-entry code compares it against `3` for broader map presence. | map presence or cargo state. |
| `+0x154` | `City_Belong_Change` assigns a city pointer; `Map_To_Battle_Army` reads `building_status[...]` through it. | stationed/associated city. |
| `+0x160` | Country army traversals follow this pointer. | next army in linked list. |

### `BattleUnit_0x64`

This is the battle-side record created from map-level `ArmyUnit_0x164_plus`
records. `BattleArmy` allocates each record as a 100-byte block, fills the
fields below, and the battle arrange/update paths later traverse the per-side
linked lists and grid pointers.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | `BattleArmy` sets it from `ArmyTypeDef.unit_class == 2`; grid code tests zero/nonzero when choosing front/back layers. | battle layer or unit-class flag. |
| `+0x04` | Battle update and stat logic index `g_army_type_table` through this field. | army type id. |
| `+0x08` | Battle interaction code compares it with opposing battle records. | owner country id. |
| `+0x0c` | Arrange/UI code checks it against the side being arranged. | battle side. |
| `+0x10/+0x14` | Arrange code initializes and places these on a `0x18`-wide battle grid; death/update code clears grid slots using them. | battle grid x/y. |
| `+0x18` | Initialized from a side-specific direction table and used by movement/action logic. | facing or direction. |
| `+0x1c` | Incremented/reset during action animation in `Do_Battle_Army_And_Battle_Die`. | action frame. |
| `+0x20` | Nonzero branches into movement/animation update paths. | moving or animating flag. |
| `+0x24/+0x28` | Battle AI writes action ids/substates such as attack and movement choices. | action state and substate. |
| `+0x2c` | Compared with `ArmyTypeDef.battle_step_frame_count`. | step frame. |
| `+0x30` | Filled from map-unit strength chunks and capped at 100; UI and damage code read it as remaining strength. | strength chunk. |
| `+0x34..0x3f` | Copied from `Map_To_Battle_Army` attack stat vector and read by battle resolution. | attack stats. |
| `+0x40..0x4b` | Copied from `Map_To_Battle_Army` defense/support stat vector and read by battle resolution. | defense stats. |
| `+0x4c` | Copied from `ArmyUnit.battle_slot_or_category`. | source battle slot/category. |
| `+0x50` | `BattleArmy` assigns the chunk index for multi-formation map armies. | formation index. |
| `+0x54` | Copied from the map army's extra id field at `+0x13c`. | map-unit extra id. |
| `+0x58` | Copied from `ArmyTypeDef.battle_sprite_or_effect_id`. | battle sprite/effect id. |
| `+0x5c` | Zeroed at allocation; list/grid maintenance touches this slot. | previous or auxiliary link. |
| `+0x60` | `Battle_AutoArrange` and arrange/UI code traverse this pointer. | next battle unit. |

### `BattleGridCell_0x30`

The battle map is a fixed 24x24 grid. The decompiler often renders fields as
`(&field_alias)[cell_index * 0xc]`; that is a Ghidra artifact from treating a
field within a `0x30`-byte cell as a separate dword/pointer array.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | `Make_Battle_Map` writes terrain ids/classes and `Decode_Battle` switches on values `0..0xe`. | terrain kind. |
| `+0x04` | `Decode_Battle` writes resolved base tile image indices such as `0x32e + terrain * 0x4d + variant`. | base tile image index. |
| `+0x08` | `Decode_Battle` writes overlay/transition image indices for terrain classes `0xb..0xe`. | overlay tile image index. |
| `+0x0c` | `Make_Battle_Map` initializes it to `-1` and later stores random terrain variant choices. | terrain variant. |
| `+0x10` | `Make_Battle_Map` writes side/region markers, commonly `-1`, `1`, or side-derived values. | battle region or owner marker. |
| `+0x14` | Arrange/update code places and clears the primary front-layer `BattleUnit_0x64 *`. | front unit. |
| `+0x18` | Battle update stores a front-layer auxiliary/moving/target unit pointer. | front auxiliary unit. |
| `+0x1c` | Arrange/update code places and clears the primary back-layer `BattleUnit_0x64 *`. | back unit. |
| `+0x20` | Battle update stores a back-layer auxiliary/moving/target unit pointer. | back auxiliary unit. |
| `+0x24` | `Do_Battle_Stone` and death/update paths store allocated effect/projectile records. | effect or projectile pointer. |
| `+0x2c` | Battle update clears this late per-cell marker during action resolution. | update marker. |

### `ArmyTypeDef_0x400`

`Load_Dat` copies the full table as `0x5b00` dwords (`0x16c00` bytes), then
derives `+0xf4` from `build_cost` for each record. City production normally
iterates the first `0x4b` trainable types, while battle/UI code can reference
higher ids.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | `Put_City_Make` and table/UI paths skip zero entries. | enabled/display flag. |
| `+0x0c` | `BattleArmy`, `Map_To_Battle_Army`, near-city scans, and battle resolution compare values `0`, `1`, and `2`. | unit class/domain. |
| `+0x10` | `City_Building` reads this when completing unit production. | land/domain flag. |
| `+0x2c` | `BattleArmy` copies it into battle record slot `0x16`. | battle sprite/effect id. |
| `+0x38` | `City_View` uses it to select the unit image. | city-view image id. |
| `+0x3c` | Battle action loops compare animation/action counters against it. | battle action frame count. |
| `+0x60` | `Load_Dat` validates mission `0x29` counter `ArmyUnit +0x12a` against it. | mission range limit. |
| `+0x90` | `Load_Dat` validates idle class-2 mission counter against it. | special mission range limit. |
| `+0xec` | Unit production UI and AI classify/order unit choices with this late table field. | build priority / AI rank. |
| `+0xf0` | `City_Building` and `Put_City_Make` compare city build progress against it. | build cost. |
| `+0xf4` | Derived by `Load_Dat` from the magnitude of `build_cost`. | build cost digit count/display width. |
| `+0xf8/+0xfc/+0x100` | `Map_To_Battle_Army`, `BattleArmy`, production UI, and city threat logic use these as primary combat numbers. | attack/combat stats A/B/C. |
| `+0x104/+0x108/+0x10c` | `Map_To_Battle_Army` mirrors these into defensive/support stat arrays. | defense/support stats A/B/C. |
| `+0x110` | `Load_Dat` caches it into `ArmyUnit +0x138` after scaling; UI displays it divided by 9. | movement/speed. |
| `+0x114` | Battle AI compares range/rank counters with this value. | battle minimum range / rank. |
| `+0x118..` | Early indexes are used by battle class interactions; city support code can render later offsets from this base in Ghidra output. | combat/support value block. |
| `+0x12c` | Transport validation in `Load_Dat`, `AI_Diplomat`, and `Map_To_Battle_Army` requires this to be nonzero for carriers. | transport capacity. |
| `+0x138` | Load repair intersects this with carried-unit capability masks. | transport mask. |
| `+0x140/+0x144` | Near-city/air and transport checks compare capability bitmasks through these fields. | capability / transportable masks. |
| `+0x160` | `Battle_AutoArrange` and `Do_Battle_Army_And_Battle_Die` compare step/action counters against it. | battle step frame count. |
| `+0x164/+0x184` | `City_Belong_Change` adds/removes shorts from city protection/resource counters while units are stationed. | city support deltas. |
| `+0x1b4/+0x1b8` | `Put_City_Make` requires these buildings completed unless they are `-1`, with several special cases. | unit prerequisite buildings. |
| `+0x1f8..` | `Put_City_Make` compares 40 resource slots against city/country resource availability. | resource cost by kind. |

### `City_0x1b8_plus`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x16` | `do_city.c`, `city_view.c`, `load_dat.c`. | city tile x. |
| `+0x18` | `do_city.c`, `city_view.c`, `load_dat.c`. | city tile y. |
| `+0x1b4` | `do_city.c` next pointer; `load_dat.c` linked-list rebuild. | next city pointer. |
| `+0x01` | Compared with `g_active_country_index`/`g_human_country_index`; `City_Belong_Change` rewrites it after ownership changes. | owner country id. |
| `+0x03..0x15` | Passed to `Format_Text` and copied into country capital-name buffers; current typed range stops before tile x/y. | city name bytes. |
| `+0x4c` | Used in city growth/event thresholds. | development/business-like stat. |
| `+0x50` | Used with safety/growth thresholds. | safety/happy-like stat. |
| `+0x54` | Used in resource/upgrade thresholds. | resource/technology-like stat. |
| `+0x5c` | `City_Building` switches on it; queue decode writes `0`, `1`, `2`, or `0xff`. | current production mode: army/building/special project/none. |
| `+0x60` | `city_building.c` accumulates it against army/building/project costs and resets after queue advance. | current build progress. |
| `+0x64..0xa4` | Indexed as `building_status[id]` across `do_city.c`, `city_building.c`, `city_building_ai.c`, `city_people_change.c`, and `city_resource_change.c`; value `2` is treated as completed. | per-city building status array. |
| `+0xa5..0xbd` | Indexed by special-project id in `city_building.c` and `city_resource_change.c`; value `2` is treated as completed. | per-city special project/wonder status array. |
| `+0xbe` | Gated in `city_building_ai.c` and `do_city.c` before special production/building cases. | special capability flag. |
| `+0xcc` | Used as population/production threshold input. | population or stored production. |
| `+0xd0` | `city_people_change.c` clamps growth to `1.0`; `city_resource_change.c` clears it when population reaches capacity. | population growth clamped flag. |
| `+0xd4` | `city_building.c` adds/removes completed building/project income entries; `city_resource_change.c` adds it into per-turn income. | building income/yield accumulator. |
| `+0xd8..0xeb` | `city_building.c` shifts these entries after production completes and decodes ranges `<0x4b`, `0x4b..0x8b`, `0x8c..0xa4`. | build queue entries. |
| `+0xec..0xff` | Parallel byte arrays shifted with `build_queue_entries` and passed to build placement helpers. | build queue x/y or placement slot bytes. |
| `+0x176` | `City_Business` iterates this many connected city links; `City_Belong_Change` decrements it when links are removed. | trade route / city link count. |
| `+0x17e` | `City_Round_Check` stores a recomputed neighbor pressure count; `City_Building_AI` tests it for isolation/pressure decisions. | nearby city pressure. |
| `+0x180` | `City_Event_Happen` clears it every time city policy/event mode changes. | event transition pending flag. |
| `+0x16a..0x16f` | `do_city.c` increments/decrements per job/resource category. | worker allocation counters. |
| `+0x183..0x1aa` | `City_Business` indexes 40 resource-like slots; value `2` in one city enables transfer/benefit to linked city. | per-resource trade state. |
| `+0x1ab` | `City_Round_Check` derives it from nearby city density; `City_Building_AI` compares it against `<2`/`!=0`. | nearby city count bucket. |
| `+0x181/+0x182` | Turn-processing flags in `do_city.c`. | already-processed flags. |

### `CountryState_0xe68`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Country table loops skip inactive rows. | `is_active`. |
| `+0x01` | Compared with `0x22` in city-event condition. | `leader_or_country_id`. |
| `+0x03` | Indexes `g_country_profile_defs`; used in city round/civil works cost modifiers. | country profile id. |
| `+0x38` | `city_building.c` writes the current city after founding/capital-class building completion; `city_building_ai.c` compares it to the current city. | capital/primary city pointer. |
| `+0x3c..0x5b` | Capital/primary city name is copied here after capital assignment. | capital name bytes. |
| `+0x5e/+0x5f` | `Diplomat_Turn` treats `+0x5e == -1` or target country as a focus condition and uses `+0x5f` as a limit. | diplomacy focus target/limit. |
| `+0x60` | Compared with `3` in city-event condition. | `government_or_ai_mode`. |
| `+0x6c` | `City_Building` skips normal production progress when positive. | production freeze / no-progress flag. |
| `+0x78/+0x79` | `city_building_ai.c` and `city_resource_change.c` gate building ids `0x0f/0x27` and `0x10/0x28`. | coastal/naval building unlock flags. |
| `+0x7a` | `city_resource_change.c` uses it with `government_or_ai_mode == 3`. | government bonus enabled flag. |
| `+0x7b` | `city_people_born_rate.c` switches on it. | population growth policy. |
| `+0x7c` | `prepare_city_doing.c` divides country pressure by it; diplomacy logic uses it in city-count checks. | owned city count. |
| `+0x1aa` | Used as a country-wide divisor/threshold in city production, city round checks, and diplomacy AI. | total force or unit count. |
| `+0x1ac..0x203` | `Diplomat_Turn`, AI diplomat code, city checks; values `2..5` are normal relations, `>5` hostile/blocked in many branches. | diplomacy state by country. |
| `+0x204/+0x2b4/+0x30c` | Per-country flags tested as a group before selecting some diplomatic actions; `+0x30c == 1` blocks several actions. | diplomacy treaty/blockade/truce flag arrays. |
| `+0x25c` | `City_Business` and `City_Round_Check` require value `1` for trade/resource interactions with a foreign city. | trade agreement flags. |
| `+0x364` | Used as the payment amount when relation state is `4`; capped by treasury and transferred between countries. | tribute/payment by country. |
| `+0x3bc/+0x414/+0x46c` | `Diplomat_Turn` compares these against leader personality thresholds to choose diplomatic actions. | affinity/caution/pressure scores by country. |
| `+0x4c4` | `prepare_city_doing.c` tests this byte flag before counting cross-country city trade output. | city trade enabled by country. |
| `+0x4da` | `Diplomat_Turn` stores action ids here immediately before starting diplomacy. | pending diplomatic action by country. |
| `+0x506` | Small byte counter reduced/reset around contact attempts in `Diplomat_Turn`. | diplomacy contact cooldown by country. |
| `+0x51c` | `Diplomat_Turn` increments and thresholds this ushort counter by country. | diplomacy turn counter by country. |
| `+0x688` | Compared against upgrade cost in `Do_City`. | `science_budget_or_treasury`. |
| `+0x698` | Increased by city stored value when a city is removed. | `population_or_score_total`. |
| `+0x6a0..0x6a3` | `city_resource_change.c` compares/scales city economic and research deltas with these byte levels. | resource/construction/research/tax efficiency levels. |
| `+0x6a4..0x713` | `city_resource_change.c` and `diplomat_steal_science.c` index words by science id; value `2` means completed. | early per-country science status array. |
| `+0x714` | Compared with `2` in city-event condition. | `country_state_mode`. |
| `+0x9c4` | Negative value blocks construction worker allocation. | `build_or_draft_capacity`. |
| `+0x9c8/+0x9cc` | `city_resource_change.c` increments both with construction-worker research output and resets `+0x9c8` on completion. | current/lifetime research progress. |
| `+0x9d4..0xa14` | Checked before city building availability in `do_city.c`, `city_building_ai.c`, and `city_people_change.c`. | available building flags. |
| `+0xa15..0xa2d` | Checked before special project construction in `city_building_ai.c`. | available special project flags. |
| `+0xa2e` | Compared with pending/special-project counts in AI build selection. | available special project count. |
| `+0xa2f..0xa86` | Indexed by army id before city army production can continue. | trainable army flags. |
| `+0xa87..0xa9f/+0xaa0` | Decremented when special-project pending counts clear. | special project pending counts and total. |
| `+0xa82/+0xa86` | Timer decremented and state set in `Do_City`. | `turn_timer`, `timer_state`. |
| `+0xe14` | `city_resource_change.c` consumes it as an accumulator/carryover and clears it when applied. | city resource carryover. |
| `+0xe18` | Gates city upgrade logic. | `upgrade_permission_level`. |

### `BuildingDef_0x200`

The building table is still not fully labeled, but these offsets are strongly
correlated by `City_Building`, `City_Build_AI_Build_Able`, `City_Upgrade`, and
the city/building tooltip in `Put_City_View`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x1c..0x5b` | City/building UI draws names from this string area. | `name_bytes`. |
| `+0x48` | `City_Upgrade` follows this id when an old building unlocks/replaces another. | `upgrade_to_building_id`. |
| `+0x4c/+0x50` | Placement and build AI multiply these values and compare map footprint. | `footprint_width_tiles`, `footprint_height_tiles`. |
| `+0x54` | Production compares city `build_progress` against this. | `build_cost`. |
| `+0x5c` | Added to city `building_income_yield` on completion and subtracted on removal. | `income_yield_delta`. |
| `+0x60/+0x64/+0x68/+0x6c` | Shown in building tooltip and applied through city stat/resource changes. | growth/business/safety/resource-or-science deltas. |
| `+0x78..0x97` | Indexed by current country/resource state when showing build cost/resource requirements. | `resource_cost_by_kind`. |
| `+0x98/+0x9c` | Displayed in the city/building tooltip and compared by AI/city checks. | population and upgrade/development requirements. |
| `+0xa0/+0xa4` | Build AI requires these prerequisite building ids unless `-1`. | prerequisite buildings. |
| `+0xec` | Production acceleration branches compare category ids `2`, `4`, `5`, `6`. | `building_category`. |
| `+0xf0` | Build-table editor and availability/display logic touch this slot. | `unlock_or_display_flag`. |

### `SpecialProjectDef_0x200`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Messages format the project name from `g_special_project_defs + id * 0x200`. | `name_bytes`. |
| `+0x38` | Production compares city `build_progress` against this. | `build_cost`. |
| `+0x40` | Added to city `building_income_yield` on completion. | `income_yield_delta`. |
| `+0x48` | Applied by `City_Resource_Change` when project ownership/effect conditions match. | `global_effect_or_score_delta`. |
| `+0xd4` | Build-table editor and availability/display logic touch this slot. | availability/display flag. |

### `ScienceDef_0x88`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Research lists skip entries where this is zero. | `is_enabled`. |
| `+0x04` | Research/diplomacy messages format this text. | `name_bytes`. |
| `+0x1c/+0x20` | Research availability checks these prerequisite science ids for completion or `-1`. | prerequisite science ids. |
| `+0x24` | Compared against `current_research_progress`. | `research_cost`. |
| `+0x28` | Used in research pacing and AI evaluation. | `era_or_group_id`. |

### `CountryProfileDef_0x7c`

`Load_Dat` reads/writes the whole static profile block as `0x3070` bytes. The
table editor calls around `0x0045ee10` expose many columns with base
`0x00596218` and stride `0x7c`; active countries reference rows through
`CountryState_0xe68 + 0x03`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00..0x10` | Profile editor text column at `0x00596218 + row * 0x7c`. | short name bytes. |
| `+0x11..0x36` | Profile editor text column at `0x00596229 + row * 0x7c`; diplomacy start formats text from here. | display name bytes. |
| `+0x24` | Editor/loader tests values `-1`, `0`, and `1`. | enabled/display flag. |
| `+0x28` | Copied into active country modifier tables in initialization paths. | profile base value. |
| `+0x40` | `City_Round_Check` subtracts this percent from city route/canal work costs. | engineering discount percent. |

## Resource Containers

`.EMG` and `.XMG` resources share a compact container shape used by
`FUN_004f8a20` and `FUN_004f8c50`:

- File begins with `uint16 group_count`.
- Each group begins with `uint16 frame_count`.
- For `.EMG`, each frame is three `uint16` values followed by
  `width_words * 2` bytes of 16-bit pixels. `FUN_004f7eb0` then converts the
  16-bit pixels into the active surface pixel format.
- `.XMG` uses the same high-level group/frame idea, but the third frame field
  can carry `0x8000`; `FUN_004f8c50` handles that alternate payload length
  before calling `FUN_004f7f1b`.

`tools/reverse_probe/emg_probe.py` parses this container and verifies that
`UI_String.EMG`, `UI_CITY.EMG`, and `MENU_ITEM.EMG` consume exactly to EOF.

## Applied Function Names

The Ghidra project now names the high-value functions using embedded debug
strings and surrounding behavior. Examples include:

- `Do_City`, `City_Round_Check`, `City_Resource_Change`,
  `City_Building_AI`, `City_Event_Happen`.
- `Load_Dat`, `Decode_City`, `Decode_NewMap`, `Do_Map`.
- `Battle_AutoArrange`, `Do_Battle_Army_And_Battle_Die`,
  `Map_To_Battle_Army`, `Start_Map_Battle_From_Army`,
  `Start_Map_Battle_From_Tile`, and `Prepare_Battle_Tile_Object_Flags`.
- `MainMenu_Init`, `PutScreen_Mainmenu`, `Present_Dirty_Rects`,
  `Load_TMG_Background`.
- Utility/render helpers such as `Trace_Function`, `Font_Select`, `Draw_Text`,
  `Draw_Text_Centered`, `Draw_Image_To_Backbuffer`,
  `Restore_DirectDraw_Surfaces`, `Report_DirectDraw_Error`, `Get_Game_Tick`,
  `Clear_Surface`, `Set_Draw_Clip_Rect`, and `Format_Text`.

## Render And Menu Globals

| Working name | Evidence | Meaning |
|---|---|---|
| `g_directdraw_ready` | Guard in `Present_Dirty_Rects`. | DirectDraw initialized/available flag. |
| `g_primary_surface` | Destination object for Blt/BltFast calls. | Front/primary DirectDraw surface. |
| `g_back_surface` | Source object for Blt/BltFast and lock/unlock. | CPU-drawn logical/back surface. |
| `g_back_surface_locked` | Unlock guard before presenting. | Back surface lock state. |
| `g_main_window` | Passed to `GetClientRect`, `ClientToScreen`, and DirectDraw error-report helpers. | Main game window handle. |
| `g_app_screen_state` | Main menu and dialog click handlers write small screen/state ids before transitions. | Application screen/state id. |
| `g_present_src_left/top/right/bottom` | Copied into source rect before present. | Source rectangle bounds. |
| `g_present_dst_rect` | Passed to surface Blt as destination rect. | Destination rectangle. |
| `g_present_clip_rect` | Clamped against client width/height. | Present clipping rectangle. |
| `g_dirty_rect_x/y` | Dirty rect position used by present path. | Current dirty rect origin. |
| `g_loaded_tmg_background` | `MainMenu_Init` loads `MAINMENU.TMG`; loaders free the previous background before replacing it. | Current decoded TMG background. |
| `g_frame_tick` / `g_menu_action_tick` | Assigned from `Get_Game_Tick` after loading and menu actions. | Frame/action timestamp counters. |
| `g_menu_item_emg_resource` / `g_mainmenu_emg_resource` | Loaded/freed around main menu EMG resources. | Main menu resource handles. |
| `g_mainmenu_anim_state` | Drives main-menu intro/normal animation branches. | Main-menu animation phase. |
| `g_mainmenu_sprite_bank` | Base pointer for menu sprite entries passed to `g_draw_sprite_fn`. | Loaded menu sprite bank. |
| `g_mainmenu_selected_index` | Selects highlighted menu item branch. | Current menu selection. |
| `g_mainmenu_highlight_frame` | Rolls over at 10 while drawing highlight sprite. | Highlight animation frame. |

## Exported High-Value Functions

Use `string_xrefs.md` for the full address-to-debug-string table. The most
important code-first files are:

- `game/load_dat.c`: save/map loading, decompression handoff, table copy, map
  dimension setup, city/army link repair.
- `game/do_city.c`: per-turn city simulation and city AI/resource/job/event
  processing.
- `game/do_battle_army_and_die.c`: battle army update and death processing.
- `game/start_map_battle_from_army.c` and
  `extra/start_map_battle_from_tile.c`: map-to-battle entry points that seed
  battle tiles, collect participating armies, and call battle setup.
- `ui/main_menu_putscreen.c`: main menu visual composition and animation.
- `render/present_dirty_rects.c`: final dirty-rect surface present.

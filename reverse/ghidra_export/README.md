# Ghidra Export Index

This directory contains reconstructed source-like output from
`China2EX_fontfix8.exe`. These files are decompiler pseudocode, not original
source code.

The current export is regenerated after a first-pass semantic annotation script
renames functions/globals and applies recovered structures for city, country,
land-tile, battle, and render state. It is no longer raw Ghidra output.

Generated with:

```powershell
powershell -ExecutionPolicy Bypass -File tools\reverse_probe\run_ghidra_export.ps1
```

Full function pseudocode can be regenerated with:

```powershell
powershell -ExecutionPolicy Bypass -File tools\reverse_probe\run_ghidra_export.ps1 -AllFunctions
```

The portable toolchain used for this export is kept inside
`tools\decompiler`:

- `ghidra_12.1.2_PUBLIC`
- optional `jdk-*` directory, or any compatible `java.exe` on `PATH`

## Top-Level Indexes

- `function_inventory.md`: Ghidra's detected function inventory with addresses,
  recovered/generated names, sizes, and outgoing-call counts.
- `string_xrefs.md`: xrefs from useful embedded debug/resource strings to code.
  This is the main bridge between raw `FUN_...` names and the game's original
  subsystem names.
- `STRUCTURE_NOTES.md`: recovered structure/global/function names and the
  evidence used to apply them.
- `UNCERTAINTIES.md`: fields whose behavior is partly understood but whose
  original UI/game label is not proven yet.
- `all_functions/*.c`: raw all-function decompiler export. This currently
  contains 1106 files, one per Ghidra-detected function. These are useful for
  coverage and search, but most are not manually named or cleaned.

## UI And Render Pseudocode

`render/*.c` contains the DirectDraw and surface pipeline:

| File | Address | Meaning |
|---|---:|---|
| `init_directdraw_runtime.c` | `0x46d310` | DirectDraw/DirectX initialization. |
| `apply_resolution_mode.c` | `0x4c2da0` | Logical resolution mode globals and offsets. |
| `lock_back_surface.c` | `0x4f0030` | Locks the CPU-drawn back surface. |
| `unlock_back_surface.c` | `0x4f0070` | Unlocks the back surface. |
| `present_dirty_rects.c` | `0x4f02d0` | Dirty-rect present path using Blt/BltFast. |
| `set_display_mode_from_mode_table.c` | `0x4f0afd` | SetDisplayMode from the static mode table. |
| `create_front_surface.c` | `0x4f0ce0` | Primary/front surface creation region. |
| `create_back_surface.c` | `0x4f0de0` | Back/logical surface creation region. |
| `init_surface_pixel_state.c` | `0x4f81e0` | Surface desc/pixel-format state setup. |
| `load_tmg_background.c` | `0x49bec0` | `GRAPH\<name>.TMG` background loader. |

`ui/*.c` contains the confirmed main-menu UI path:

| File | Address | Meaning |
|---|---:|---|
| `main_menu_init.c` | `0x478eb0` | Main-menu resource and viewport init. |
| `main_menu_quit.c` | `0x479000` | Main-menu cleanup. |
| `main_menu_putscreen.c` | `0x479040` | Main-menu drawing and animation. |
| `main_menu_mouse_left_release.c` | `0x479420` | Main-menu click/release handler. |

## Game Logic Pseudocode

`game/*.c` contains currently exported high-value main logic. The names come from
embedded debug strings and `string_xrefs.md`.

| Group | Representative files |
|---|---|
| Battle | `battle_auto_arrange.c`, `do_battle_army_and_die.c`, `battle_army.c`, `decode_battle.c`, `make_battle_map.c`, `battle_arrange_position_and_ui_load.c` |
| City simulation | `do_city.c`, `city_round_check.c`, `city_resource_change.c`, `city_building.c`, `city_building_ai.c`, `calc_city_resource.c`, `calc_city_job_people.c` |
| City UI/events | `city_view.c`, `event_city_view.c`, `city_event_happen.c`, `city_manager.c` |
| Diplomacy | `diplomat_battle_back.c`, `diplomat_end_battle_back.c` |
| Map/save load | `load_dat.c` |

## Extra Xref-Driven Exports

`extra/*.c` is a second sweep from `string_xrefs.md`. It includes additional
code paths whose names are exposed by embedded strings:

| Group | Representative files |
|---|---|
| Decode/map rendering | `decode_city.c`, `decode_new_map.c`, `decode_long_wall.c`, `decode_road.c`, `decode_minimap.c` |
| Diplomacy AI/order UI | `ai_diplomat.c`, `do_country_diplomat.c`, `order_diplomat_choice_mission.c`, `order_diplomat_sel_take_city.c` |
| City/map helpers | `do_map.c`, `make_city_map.c`, `make_city_wall.c`, `map_to_battle_army.c`, `near_city_found_xy.c` |
| UI helpers | `load_ui_string_emg_xmg.c`, `ui_yes_no_dialog_a.c`, `put_city_view.c`, `put_city_citizen.c`, `load_ui_dip_emg.c` |

## Current Boundary

The export is beyond raw disassembly and beyond raw Ghidra pseudocode: the
current project applies `GhidraSemanticAnnotate.java` before exporting. The
remaining limits are semantic, not tooling setup:

- Some globals and struct fields still have generated names where behavior was
  not strong enough to label.
- Original C/C++ source types are not recoverable automatically; current structs
  are evidence-based reconstructions.
- Some large functions, especially `load_dat.c` and battle/city AI routines,
  need additional field-by-field propagation before they become clean source.
- The `all_functions` export covers every Ghidra-detected function, but it is
  not equivalent to original source. It still lacks original comments, local
  variable names, file/module boundaries, exact class layouts, and some type
  signatures.

The most productive next manual step is correlating `UI_String.EMG`,
`UI_CITY.EMG`, and the city screen with the remaining ambiguous city stat and
worker fields listed in `UNCERTAINTIES.md`.

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
| `BattleUnit_approx` | Battle logic uses `param_1[4]`, `param_1[5]`, `param_1[6]` as grid x/y/type-like fields. | Battle-side army/unit record. |
| `Image/Sprite bank` | Main menu and UI paths call function pointer `DAT_00771f34` with entries from `DAT_00707f90`, and load `.EMG`/`.XMG` resources. | Decoded sprite/image resources. |

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

## Useful Offsets

### `LandTile_0x100`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x10` | `load_dat.c` checks and counts. | city/land occupancy count or resource count. |
| `+0x28` | `load_dat.c` stores pointers indexed by `army_slot * 4`. | army pointer list A. |
| `+0x50` | `load_dat.c` checks tile count/list. | army/unit count or city count. |
| `+0x54` | `load_dat.c` stores pointers indexed by slot. | army pointer list B. |
| `+0x7c` | `do_city.c`, `city_building.c`, and `city_people_change.c` add/check it beside the primary occupant count. | secondary occupant/defender count. |
| `+0x88` | `load_dat.c` dereferences during map repair. | linked record pointer or terrain object. |

### `City_0x1b8_plus`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x16` | `do_city.c`, `city_view.c`, `load_dat.c`. | city tile x. |
| `+0x18` | `do_city.c`, `city_view.c`, `load_dat.c`. | city tile y. |
| `+0x1b4` | `do_city.c` next pointer; `load_dat.c` linked-list rebuild. | next city pointer. |
| `+0x4c` | Used in city growth/event thresholds. | development/business-like stat. |
| `+0x50` | Used with safety/growth thresholds. | safety/happy-like stat. |
| `+0x54` | Used in resource/upgrade thresholds. | resource/technology-like stat. |
| `+0x60` | `city_building.c` accumulates it against army/building/project costs and resets after queue advance. | current build progress. |
| `+0x64..0xa4` | Indexed as `building_status[id]` across `do_city.c`, `city_building.c`, `city_building_ai.c`, `city_people_change.c`, and `city_resource_change.c`; value `2` is treated as completed. | per-city building status array. |
| `+0xa5..0xbd` | Indexed by special-project id in `city_building.c` and `city_resource_change.c`; value `2` is treated as completed. | per-city special project/wonder status array. |
| `+0xbe` | Gated in `city_building_ai.c` and `do_city.c` before special production/building cases. | special capability flag. |
| `+0xcc` | Used as population/production threshold input. | population or stored production. |
| `+0xd0` | `city_people_change.c` clamps growth to `1.0`; `city_resource_change.c` clears it when population reaches capacity. | population growth clamped flag. |
| `+0xd4` | `city_building.c` adds/removes completed building/project income entries; `city_resource_change.c` adds it into per-turn income. | building income/yield accumulator. |
| `+0xd8..0xeb` | `city_building.c` shifts these entries after production completes and decodes ranges `<0x4b`, `0x4b..0x8b`, `0x8c..0xa4`. | build queue entries. |
| `+0xec..0xff` | Parallel byte arrays shifted with `build_queue_entries` and passed to build placement helpers. | build queue x/y or placement slot bytes. |
| `+0x16a..0x16f` | `do_city.c` increments/decrements per job/resource category. | worker allocation counters. |
| `+0x181/+0x182` | Turn-processing flags in `do_city.c`. | already-processed flags. |

### `CountryState_0xe68`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Country table loops skip inactive rows. | `is_active`. |
| `+0x01` | Compared with `0x22` in city-event condition. | `leader_or_country_id`. |
| `+0x38` | `city_building.c` writes the current city after founding/capital-class building completion; `city_building_ai.c` compares it to the current city. | capital/primary city pointer. |
| `+0x60` | Compared with `3` in city-event condition. | `government_or_ai_mode`. |
| `+0x7c` | `prepare_city_doing.c` divides country pressure by it; diplomacy logic uses it in city-count checks. | owned city count. |
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
| `+0xe18` | Gates city upgrade logic. | `upgrade_permission_level`. |

## Applied Function Names

The Ghidra project now names the high-value functions using embedded debug
strings and surrounding behavior. Examples include:

- `Do_City`, `City_Round_Check`, `City_Resource_Change`,
  `City_Building_AI`, `City_Event_Happen`.
- `Load_Dat`, `Decode_City`, `Decode_NewMap`, `Do_Map`.
- `Battle_AutoArrange`, `Do_Battle_Army_And_Battle_Die`,
  `Map_To_Battle_Army`.
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
- `ui/main_menu_putscreen.c`: main menu visual composition and animation.
- `render/present_dirty_rects.c`: final dirty-rect surface present.

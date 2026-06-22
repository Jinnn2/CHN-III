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
| `g_science_priority_target_ids[12]` | `Before_Edit_Science_Power` backs up and edits 12 dwords at `0x00581778`; `Science_Next` splits them into two six-entry groups before consulting per-science priority weights. | Science AI/research-priority target table. |
| `g_flag_img_bank` | `Load_EMG_Base` loads `FLAG.IMG` through `Safe_LoadIMG`; `Load_Dat` copies 100 `0x100`-byte flag blocks through this bank, and the flag editor modifies pixels inside the selected block. | Empire/country flag IMG resource bank. |
| `CountryProfileDef_0x7c` | Static table starts at `0x00596218`; `load_dat.c` reads/writes `0x3070` bytes, i.e. 100 records of `0x7c`; country `+0x03` indexes this table. | Country/civilization profile and modifier table. |
| `EmpireCountryDef_0x200` | Static table starts at `0x00589a18`; `Before_Edit_Empire_Country` reads/writes `EMPIRE.DAT` as `0xc800` bytes, i.e. 100 records of `0x200`; active countries store ids into this table. | Empire/country/leader definition table. |
| `GovernmentDef_0x74` | Static table starts at `0x00599288`; `Load_Dat` copies `0x3a0` bytes, i.e. 8 records of `0x74`; country `government_or_ai_mode` indexes this table. | Government/civic modifier table. |
| `GroundDef_0x24` | Static table starts at `0x00589428`; `Load_Dat` copies `0x21c` bytes, i.e. 15 records of `0x24`; `Before_Edit_Ground` binds editor controls to the same stride. | Ground/terrain definition table. |
| `ArmyTypeDef_0x400` | `Load_Dat` reads `0x16c00` bytes into `g_army_type_table`, i.e. 91 records of `0x400`; map armies index this table by `army_type_id`. | Static unit/army definitions. |
| `BattleGridCell_0x30` | `Make_Battle_Map` clears `0x6c00` bytes from `g_battle_grid_cells`, i.e. `24 * 24 * 0x30`; battle arrange/update paths address cells by `x + y * 0x18`. | One cell in the 24x24 battle grid. |
| `MapScenarioInfo_0x16c` | `Load_Map_GameInfo` reads custom-map metadata in `0x16c` records; `Load_Dat` reads the same shape into `g_current_map_scenario_info`; `Before_Window_Edit_File_Detail` builds an editor form over the current record. | Map/scenario header and editor-visible rules. |
| `DataFormat_0xc8` | `Add_New_DataFormat` allocates 200 bytes tagged `DATA_FORMAT`; `NodeInsert_DataFormat` links nodes through `+0xbc/+0xc0` and computes option/list layout by `control_type`. | Window/form field descriptor for editor/table controls. |

## Important Globals

| Address/global | Evidence | Working meaning |
|---|---|---|
| `g_land_tiles` | `load_dat.c`, `do_city.c` tile address arithmetic. | Base pointer for `LandTile_0x100[]`. |
| `g_map_width_tiles` | Map width-like dimension after `load_dat.c` map-size switch. | Map width in tiles. |
| `g_map_height_tiles` | Map height-like dimension after `load_dat.c` map-size switch. | Map height in tiles. |
| `g_search_round_best_score` | `Search_Round` clears it, `Search_Round_Candidate` raises it when a scanned radius tile is a better target, and AI branches require it positive before using the result. | Best score from the current AI radius scan. |
| `g_search_round_best_tile_x/y` | Written by `Search_Round_Candidate` with the selected candidate tile; AI army/ship/air paths assign these to unit target coordinates. | Best target tile from `Search_Round`. |
| `g_search_round_best_radius_left` | Set from the radius-offset entry that produced the winning candidate; air/ship AI subtracts it from movement range. | Remaining radius/movement value for the best search result. |
| `g_search_round_first_enemy_tile_x/y` | Initialized to `-1`; set when `Search_Round_Candidate` sees the first enemy or hostile city army tile. | Fallback hostile tile from a radius scan. |
| `g_search_round_*_count/power` | `Search_Round_Candidate` accumulates friendly/enemy visible unit counts and weighted power totals while scanning. | Radius-scan force summary counters. |
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
| `g_empire_country_defs` | `0x00589a18`, 100 records, `0x200` byte stride. | Static empire/country/leader definitions. |
| `g_government_defs` | `0x00599288`, 8 records, `0x74` byte stride. | Static government/civic modifier definitions. |
| `g_ground_defs` | `0x00589428`, 15 records, `0x24` byte stride. | Static ground/terrain definitions. |
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
| `g_map_interaction_mode` | `PlayGame_Init` sets normal map mode `1`; city/diplomacy paths set other modes; `Edit_Start` sets `99` and `Edit_Finish` restores `1`. | Current map/input interaction mode. |
| `g_current_land_tile` | Editor left/right-click handlers and `Load_Dat` use this as the selected/hovered tile pointer. | Current map tile under interaction. |
| `g_editor_cursor_tile_x/y` | `MLR_Edit_GameMap`, editor press handlers, and keyboard hover tracking validate these against map dimensions before editing or previewing a tile. | Current editor cursor tile coordinates. |
| `g_editor_land_tile_backup` | `Edit_Start` allocates `width * height * 0x100` bytes under `Edit_MAP_TYPE_BackUp`; `Edit_Finish` frees it. | Whole-map tile backup for editor mode. |
| `g_editor_tool_mode` | Editor mouse handlers switch on this value; left/right press and release paths give different behavior to modes `1`, `2`, `3`, `5`, `6`, `7`, `8`, `9`, and `0xb`. | Current editor map tool. |
| `g_editor_brush_size_index` | Press/drag handlers map this through `{0,1,2,4}` and then into brush offset/count tables at `0x0074c830`/`0x0074a360`. | Editor brush radius/shape selector. |
| `g_tile_radius_offset_counts` | Editor brush loops, near-city scans, and AI range checks use this as the count side of shared tile-radius offset tables. | Number of x/y offsets for each tile-radius pattern. |
| `g_edit_dest_round_buffers` | Allocated/freed as `DestRound_0/1`; editor brush code indexes them by y parity and reads `short x, short y` pairs. | Parity-specific tile-radius offset buffers. |
| `g_request_redraw` | Frame pumps, dialog handlers, and editor mutations set this before `Present_Dirty_Rects` decides whether to redraw/present. | Global redraw request flag. |
| `g_editor_left_press_active` | `Read_MLP_Edit` gates left-button map editing on this flag. | Left mouse press/drag active in the editor. |
| `g_editor_form_input_blocked` | Editor data-format finalizers clear it; right-click map editing is blocked while it is nonzero. | Modal/form input blocks map editing. |
| `g_editor_map_backup_state` | Left/right press handlers set it before copying `g_land_tiles` into `g_editor_land_tile_backup`; release/keyboard paths advance/reset it. | Editor transaction/undo backup state. |
| `g_editor_selected_country_id` | City/unit/ownership tools validate it against `0..0x15` and use it to create cities, create armies, and paint owner/visibility bytes. | Selected country/faction for editor tools. |
| `g_editor_selected_city_resource_id` | Resource tool `6` assigns it to `LandTile_0x100 +0x17`; hover/render code validates it before drawing a resource preview. | Selected city resource/feature id. |
| `g_edit_menu_page` | `Menu_EditMenu_Init` resets it to `0`; `MLR_NewEdit` advances it through pages `0`, `1`, and `2` for new-map editing choices. | New editor-menu page/step. |
| `g_edit_menu_selected_mode` | `MLR_NewEdit` sets it from the hovered item on page `0`; `Menu_EditMenu_Quit` treats value `0` as the new-map generation path. | New editor menu mode choice. |
| `g_edit_menu_selected_map_size` | Selected on page `1` and passed with the template choice to the map-generation helper. | New map size choice. |
| `g_edit_menu_selected_template` | Selected on page `2` and passed with the map-size choice to the map-generation helper. | New map template/seed choice. |
| `g_current_map_scenario_info` | `Load_Dat` reads a `0x16c` header here; the edit-file-detail form binds controls to fields in this record. | Current loaded map/scenario header. |
| `g_custom_map_table` / `g_custom_map_count` | `MLR_Edit_SelCustomMap` indexes `MapScenarioInfo_0x16c[]`, loads a selected map, and compacts the table after deletion. | Custom/editable map list. |
| `g_selected_custom_map_index` | Set from `g_custom_map_hover_index`; drives load, delete, and list compaction in `MLR_Edit_SelCustomMap`. | Selected custom map row. |
| `g_data_format_list_head` / `g_data_format_list_tail` | `NodeInsert_DataFormat` appends `DataFormat_0xc8` nodes, `NodeDelete_DataFormat` unlinks them, and `Del_DataFormat` removes all controls for one owner window/context. | Active window/form data-format linked list. |

## Editor And Startup

The map/editor route is now a useful recovery entry point. `App_WinMain_Entry`
calls `Process_CommandLine_Args`, then `Init_SetUp`, and then sends the app
directly to screen state `0x24` when `g_editor_mode_enabled == 1`.

| Working name | Evidence | Meaning |
|---|---|---|
| `g_editor_mode_enabled` | `Process_CommandLine_Args` sets it when the command line contains `EDIT`; `Decode_NewMap`, `City_Manager`, and `Put_City_Make` branch on it; the main entry switches to state `0x24` when it is set. | Editor/map-edit mode flag. |
| `Process_CommandLine_Args` | Trace string `Argument_Process`; parses options such as `SERVER`, `LOAD`, `DEMO`, `SIMPLE`, `ENGLISH`, `NOTEACH`, and `EDIT`. | Startup command-line option parser. |
| `Init_SetUp` | Trace string `Init_SetUp`; initializes DirectDraw, loads `EDIT_IMG`, `METAL.EMG`, `NEWUI.EMG`, mouse/UI resources, fonts, and startup data. | Main application setup and resource loading. |
| `App_WinMain_Entry` | Creates the app mutex, calls command-line/setup routines, chooses initial `g_app_screen_state`, then runs the Windows message loop. | Main WinMain-style entry function. |
| `App_Frame_Pump` | Default idle-loop frame pump used when `g_app_screen_state != 0x25`; updates frame timing, reads input, dispatches `Read_Keyboard`, draws, and presents. | Non-game/main-menu frame loop. |
| `Game_Frame_Pump` | Idle-loop frame pump used when `g_app_screen_state == 0x25`; updates game/map timers, dispatches `Read_Keyboard`, redraws active map UI, and can call `Prepare_City_Doing`. | In-game/map/editor frame loop. |
| `Menu_EditMenu_Init` | Trace string `Menu_EditMenu_Init`; loads `DRAGON` background, sets screen state `0x16`, and resets the editor menu page. | Editor/new-map menu setup. |
| `Put_Sub_EditMenu` | Trace string `Put_Sub_EditMenu`; draws the three-step editor menu using `g_edit_menu_page`, hover index, and selected mode/map-size/template values. | Editor menu draw routine. |
| `MLR_NewEdit` | Trace string `MLR_NewEdit`; handles editor menu clicks. It either delegates to custom-map selection or advances/selects the three new-map menu pages before entering state `0x17`. | Editor menu click handler. |
| `Menu_EditMenu_Quit` | Trace string `Menu_EditMenu_Quit`; when the new-map path is confirmed, enables editor mode, calls the map-generation helper with size/template selections, allocates the editor tile backup, and enters screen state `3`. | Transition from editor menu into map editing. |
| `MouseOn_Edit_Sel_Custom_Map` | Trace string `MouseOn_Edit_Sel_Custom_Map`; tracks hover over up to 20 custom-map list rows and sets action ids `0`, `1`, or `2` for load/delete/close buttons. | Custom-map picker hover handler. |
| `MLR_Edit_SelCustomMap` | Trace string `MLR_Edit_SelCustomMap`; selects a custom map, loads it through `Load_Dat`, enables editor state/backup allocation, or deletes the map and associated sidecar files before compacting the list. | Custom-map picker click handler. |
| `Load_Map_GameInfo` | Trace string `Load_Map_GameInfo`; reads custom-map scenario headers, handles older `0x168` payloads, and stores modern records as `MapScenarioInfo_0x16c`. | Custom-map/scenario header loader. |
| `Before_Window_Edit_File_Detail` | Trace string `Before_Window_Edit_File_Detail`; initializes defaults and creates form controls bound to `g_current_map_scenario_info`. | Scenario/map-detail editor form setup. |
| `Put_Edit_File_Detail` | Trace string `Put_Edit_File_Detail`; draws the scenario/map-detail window and highlights action buttons through `g_custom_map_action`. | Scenario/map-detail editor renderer. |
| `Read_MLP_Edit` | Trace string `Read_MLP_Edit`; handles left-button press/drag painting, backs up the map on first mutation, applies terrain/road/overlay/resource/ownership tools, and marks `g_request_redraw`. | Map editor left-button paint dispatcher. |
| `Read_MRP_Edit` | Trace string `Read_MRP_Edit`; handles right-button press/drag erasing, removing linked cities, armies, overlays, city resources, and ownership/visibility flags through the same radius-offset buffers. | Map editor right-button erase dispatcher. |
| `Read_MRR_Edit` | Trace string `Read_MRR_Edit`; handles right-button release by opening linked records, clearing editor named points, or confirming army removal. | Map editor right-button release dispatcher. |
| `MLR_Edit_GameMap` | Trace string `MLR_Edit_GameMap`; handles single-click placement for cities, armies, long-wall overlays, city resources, editor named points, and template stamps. | Map editor map-click placement dispatcher. |
| `Irrigate_Able` | Trace string `Irrigate_Able`; checks terrain definition flags, no linked record, and neighboring water/irrigation markers before allowing overlay action `0`; callers consume the low byte as a boolean. | Tile irrigation placement predicate. |
| `Pasturage_Able` | Trace string `Pasturage_Able`; checks terrain definition support and no city/link record before overlay action `1`; callers consume the low byte as a boolean. | Tile pasture placement predicate. |
| `Mine_Able` | Trace string `Mine_Able`; accepts road/rail-like base states and no linked record before overlay action `2`; callers consume the low byte as a boolean. | Tile mine placement predicate. |
| `Fish_Able` | Trace string `Fish_Able`; checks terrain/resource markers for fishable water or coast-like tiles before overlay action `3`; callers consume the low byte as a boolean. | Tile fishing placement predicate. |
| `Bridge_Able` | Trace string `Bridge_Able`; requires bridge-capable terrain image range and no linked record, then returns a bridge/tile-object value checked as positive by callers. | Tile bridge placement value helper. |
| `LongWall_Able` | Trace string `LongWall_Able`; requires no long-wall marker, no linked record, positive city/link count, and no region marker; callers consume the low byte as a boolean. | Tile long-wall placement predicate. |
| `Resource_Able` | Trace string `Resource_Able`; validates selected resource id against terrain/resource tables before accepting city resource tool `6`. | Tile resource placement predicate. |
| `Clear_Mountain` | Trace string `Clear_Mountain`; clears mountain/height road markers over radius pattern `1` and refreshes affected tiles. | Editor helper for clearing mountain-style tile overlay state. |
| `Cancel_All_Army_On_Tile` | Trace string misspells `Cancle_All_Army`; removes up to ten army pointers from a tile and clears owner bytes when empty. | Editor helper for deleting all armies on a tile. |
| `Make_New_Work` | Trace string `Make_New_Work`; writes the tile work kind at `LandTile +0x1a`, resets progress/state bytes, and is used by both editor overlay actions and unit turn jobs. | Starts or completes a tile work/improvement state. |
| `Make_New_Make` | Trace string `Make_New_Make`; writes road/overlay/long-wall/terrain make fields, propagates adjacent road markers, and refreshes affected map/road/long-wall tiles. | Applies finished tile construction/overlay state. |
| `Clear_Forest_Or_Resource` | Trace string `Forset_Disappear`; clears tile feature id `+0x16`, optionally clears city resource id `+0x17`, and awards resource value to the active country. | Removes forest/feature/resource state from a tile. |
| `Do_Army_TurnJob` | Trace string `Do_Army_TurnJob`; advances per-army map jobs and calls `Make_New_Work`, `Make_New_Make`, and `Clear_Forest_Or_Resource` when progress thresholds are met. | Per-turn map-work completion loop. |
| `Order_Check` | Trace string `Order_Check`; builds available command/order menu entries from unit type, tile state, improvement predicates, and current resources. | Active unit order availability builder. |
| `Order_Follower_UseAble` | Trace string `Order_Follower_UseAble`; writes selected action ids into `ArmyUnit.mission_action_id` for normal/follower orders, with extra transport/cargo validation for order ids `0x41/0x47`. | Applies an order id to a follower/cargo-capable unit when the unit can accept it. |
| `Order_Spy_Choice_Mission` | Trace string `Order_Spy_Chouice_Mission`; branches through buy-city, ask-surrender, steal-science, scare, sabotage-building, and commotion helpers, then sets spy result action ids `0x37/0x38/0x39`. | Spy mission picker/result dispatcher. |
| `Order_Forset` | Trace string `Order_Forset`; looks for adjacent enemy/known units and special project/city states, then schedules battle, forest/action, or cleanup orders through the order executor. | Forest/rest-like order handler that can interrupt into combat or city support. |
| `Order_Go` | Trace string `Order_Go`; follows queued path coordinates, handles no-path/enemy-blocked cases, and remaps pending build actions `0x17/0x18/0x19` back to executable actions `0x14/0x15/0x16`. | Main queued movement/path-follow order handler. |
| `Order_Go_Act` | Trace string `Order_Go_Act`; executes queued path steps with the alternate movement executor and emits no-path/arrived events. | Active movement step executor. |
| `Order_Guard` | Trace string `Order_Guard`; checks nearby known enemy/city threats, special project and carrier/city constraints, and either schedules an interrupt action or leaves the unit waiting. | Guard/sentry order handler. |
| `Order_Join_Sel` | Trace string `Order_Join_Sel`; builds a same-tile list of compatible uncarried units, joins immediately when only one target exists, otherwise opens the join-selection form. | Select one compatible unit to join/merge with. |
| `Order_Join_All` | Trace string `Order_Join_All`; iterates same-tile compatible idle units and joins each into the current unit before scheduling completion action `0x53`. | Join/merge all compatible same-tile units. |
| `Order_Out` | Trace string `Order_Out`; unloads one carried subunit or opens the unload-selection form, then schedules result action `0x56`. | Select one carried unit to unload. |
| `Order_Out_All` | Trace string `Order_Out_All`; unloads all same-tile units whose `transport_parent` is the current unit, then schedules result action `0x57`. | Unload all carried units. |
| `Add_OrderQueue_Army` | Trace string `Add_OrderQueue_Army`; marks `ArmyUnit.map_presence_or_cargo_state`, requests redraw for the active unit, and forwards to `Apply_OrderQueue_Army`. | Public order queue/state setter for one unit. |
| `Apply_OrderQueue_Army` | Called by every order path; writes `ArmyUnit.mission_action_id`, event/result bytes, direction, related-army pointer, and target coordinates, with special handling for transport, capture, path, and map-work actions. | Core unit order-state applier and side-effect dispatcher. |
| `Order_Nothing` | Trace string `Order_Nothing`; dispatches idle/current action ids to AI executors (`AI_Army`, `AI_AirPlane`, `AI_Ship`, `AI_Worker`, etc.) and schedules fallback orders when a unit has no immediate action. | Per-unit idle/action dispatcher. |
| `AI_Army` | Trace string `AI_Army`; ground-unit AI executor used for many normal action ids from `Order_Nothing`. | Ground army automatic action handler. |
| `AI_AirPlane` / `AI_AirOilPlane` | Trace strings `AI_AirPlane` and `AI_AirOilPlane`; select city/capable targets, path toward them, and enqueue movement or refuel-style actions. | Air-unit automatic action handlers. |
| `AI_Ship` / `AI_ActShip` / `AI_Carrier` / `AI_Transport` | Trace strings identify ship, active ship, carrier, and transport handlers; they coordinate passenger/cargo state, nearby ports/cities, and route targets through `Add_OrderQueue_Army`. | Naval and carrier/transport automatic action handlers. |
| `AI_Worker` | Trace string `AI_Worker`; searches nearby owned cities/tiles and enqueues worker map actions or fallback orders. | Worker automatic action handler. |
| `AI_UnClear` | Trace string `AI_UnClear`; scans known enemy/target lists and retargets selected units toward a chosen enemy/city objective. | Target-clearing / offensive objective AI handler. |
| `JoinTo` | Trace string `JoinTo`; validates total subunit count, moves child units from the source army to the target, adds cached stats into the target, marks both units dirty, and updates country point state. | Merge/join one army into another. |
| `BreakOut` | Trace string `BreakOut`; detaches an army from its parent or breaks carried child units out of a carrier/group, rewrites transport links, recomputes cached stats, and restores view coverage. | Split/unload unit or carried stack from a carrier/group. |
| `Add_New_View` | Trace string `Add_New_View`; increments per-country tile visibility/coverage bytes around a unit or city and refreshes minimap-visible state for the human country. | Add unit/city vision footprint. |
| `Del_Army_View` | Trace string `Del_Army_View`; decrements the same visibility/coverage bytes and refreshes the human minimap when a unit leaves a tile or changes state. | Remove unit vision footprint. |
| `Find_Direct` | Trace string `Find_Direct`; compares source/destination tile deltas, handling horizontal wrap bands by map size, and returns direction index `0..7` or `-1`. | Neighbor direction resolver. |
| `TestRoad` | Trace string `TestRoad`; validates/generates the path from an army's current tile to its target tile, filling queued path steps and clearing the path count on failure. | Army pathfinding / route validation. |
| `Army_Belong_Change` | Trace string `Army_Belong_Change`; removes an army from old-country counts/visibility, changes `owner_country_id`, updates city stats and country unit counts, then restores visibility for the new owner. | Army ownership transfer. |
| `City_Capture_Transfer` | Called from the order applier when an army enters a capturable city; transfers population/economy/science effects and emits human-facing capture messages. | City capture/transfer outcome. |
| `CountryPoint_Minus` | Trace string `CountryPoint_Minus`; decrements a country point/unit-action counter and requests UI/turn refresh when it reaches zero. | Country action/point counter decrement helper. |
| `NewLand_Name` | Trace string `NewLand_Name`; names or announces newly discovered land regions and records the name at the target coordinates. | New land/region naming side effect. |
| `Add_New_Explode` | Trace string `Add_New_Explode`; maintains up to ten per-country explosion markers, pruning stale known-region entries before adding a new tile. | Explosion/event marker queue. |
| `MouseOn_Edit_Sel_Pcx_File` | Trace string `MouseOn_Edit_Sel_Pcx_File`; maps mouse position to a 10-row PCX/file list hover index and three action-button states. | PCX/file selection hover handler. |
| `Add_New_DataFormat` | Trace string `Add_New_DataFormat`; allocates and initializes a `DataFormat_0xc8` node, copies the display label, stores binding pointers, and inserts it into the active form list. | Generic form/table control descriptor builder. |
| `NodeInsert_DataFormat` | Trace string `NodeInsert_DataFormat`; appends a descriptor to the data-format linked list and derives list/scrollbar geometry for list-like control types. | Generic form/table descriptor insertion/layout helper. |
| `NodeDelete_DataFormat` | Trace string `NodeDelete_DataFormat`; unlinks one `DataFormat_0xc8` node from the global list, frees copied label text, and frees the descriptor. | Generic form/table descriptor deletion helper. |
| `Del_DataFormat` | Trace string `Del_DataFormat`; walks the global descriptor list and deletes every `DataFormat_0xc8` node whose owner/context pointer matches the argument. | Generic form/table teardown by owner. |
| `Reflash_DataFormat` | Trace string `Reflash_DataFormat`; refreshes descriptors whose row-index source matches the argument, recomputing bound data pointers from stride/base/row fields. | Generic form/table binding refresh. |
| `CheckPress_DataFormat` | Trace string `CheckPress_DataFormat`; scans active descriptors, hit-tests mouse coordinates by control type, and writes the selected/toggled/edited value back through the descriptor's bound pointer. | Generic form/table mouse-press dispatcher. |
| `Before_Edit_Army` | Trace string `Before_Edit_Army`; backs up `g_army_type_table`, checks `ARMYBASE.DAT`, creates the table scrollbar, and binds editor controls to `ArmyTypeDef_0x400` offsets. | Unit/army definition table editor setup. |
| `Before_Edit_Build` | Trace string `Before_Edit_Build`; backs up `g_building_defs`, checks `BUILD.DAT`, creates the table scrollbar, and binds editor controls to `BuildingDef_0x200` offsets. | Building definition table editor setup. |
| `Before_Edit_Empire_Country` | Trace string `Before_Edit_Empire_Country`; reads/writes `EMPIRE.DAT`, backs up `g_empire_country_defs`, and binds controls to `EmpireCountryDef_0x200`. | Empire/country/leader definition table editor setup. |
| `After_Edit_Country` | Trace string `After_Edit_Country`; tears down the country edit form and adjusts `CountryState_0xe68 +0x6a1/+0x6a2/+0x6a3` until the three efficiency byte levels sum to `10`. | Country efficiency editor finalizer. |
| `MLP_Edit_Empire_Country` | Trace string `MLP_Edit_Empire_Country`; maps mouse hits on three vertical palette strips to `EmpireCountryDef_0x200 +0x120/+0x124/+0x128`. | Empire/country color-layer mouse editor. |
| `Before_Edit_Goverment` | Trace string `Before_Edit_Goverment`; backs up `g_government_defs`, checks `GOVERMENT.DAT`, and binds controls to the `GovernmentDef_0x74` table. | Government/civic modifier table editor setup. |
| `Before_Edit_Ground` | Trace string `Before_Edit_Ground`; backs up `g_ground_defs`, checks `GROUND.DAT`, and binds controls to the `GroundDef_0x24` table. | Ground/terrain definition table editor setup. |
| `Before_Edit_Empire_Hero` | Trace string `Before_Edit_Empire_Hero`; reads/writes `HERO.DAT`, backs up `g_country_profile_defs`, binds editor controls to `CountryProfileDef_0x7c`, and previews `DIP_%02d` resources. | Country profile / hero definition table editor setup. |
| `Before_Edit_Science_Power` | Trace string `Before_Edit_Science_Power`; backs up `g_science_priority_target_ids` and binds 12 editable dword controls. | Science priority/power target editor setup. |
| `Before_Edit_Science_Set` | Trace string `Before_Edit_Science_Set`; inspects the selected country's 200-entry science status array and the selected `ScienceDef_0x88` prerequisites to set editor toggles. | Per-country science availability/status editor setup. |
| `Put_Edit_Science_Exp` | Trace string `Put_Edit_Science_Exp`; draws the selected science's displayed value plus any unlocked army, building, or special-project names from `ScienceDef_0x88`. | Science editor explanation/preview renderer. |
| `Before_Edit_Empire_Flag` | Trace string `Before_Edit_Empire_Flag`; allocates 100 temporary `0x100`-byte image backups and copies each current flag image block from `g_flag_img_bank`. | Empire/country flag editor setup. |
| `After_Edit_Empire_Flag` | Trace string `After_Edit_Empire_Flag`; compares each backup with the live flag block, prompts to save changed pixels, restores on cancel, and frees the temporary backups. | Empire/country flag editor teardown. |
| `Save_IMG_Flag` | Trace string `Save_IMG_Flag`; writes a two-byte count (`100`) plus 100 live `0x100`-byte flag blocks to `FLAG.IMG`, then reloads the IMG resource bank. | Empire flag IMG persistence. |
| `MLP_Edit_Empire_Flag` | Trace string `MLP_Edit_Empire_Flag`; maps mouse position/color-channel selectors to a selected 14-wide flag block and writes a 16-bit pixel color. | Empire flag pixel edit handler. |
| `Clear_UnUsed_Science` | Trace string `Clear_UnUsed_Science`; after loading the science block, disables entries with empty names and resets prerequisites / related science links to `-1`. | Science definition cleanup. |
| `Science_Know` | Trace string `Science_Know`; grants or marks science state based on prerequisite completion and cascades newly available/known science entries. | Science knowledge/status transition. |
| `Science_Know_With_Prerequisites` | Called by the map editor's city creation path; starts from one science id, walks `ScienceDef_0x88.prerequisite_science_a/b`, and calls `Science_Know` for every required science reached. | Bulk science grant including prerequisite chain. |
| `Science_Next` | Trace string `Science_Next`; collects available science entries and scores AI choices using `g_science_priority_target_ids` plus per-science weight blocks. | Next research selection. |
| `PlayGame_Init` | Trace string `PlayGame_Init`; loads/initializes map state, calls `Edit_Start` when `g_editor_mode_enabled != 0`, then switches to `g_app_screen_state = 0x25`. | Game/map-mode startup. |
| `Edit_Start` | Trace string `Edit_Start`; sets map mode marker `99`, allocates `Edit_MAP_TYPE_BackUp` as `width * height * 0x100`, and enables editor-related map flags. | Editor-mode startup and map backup setup. |
| `Edit_Finish` | Trace string `Edit_Finish`; frees the editor tile backup, clears `g_editor_mode_enabled`, restores map/UI flags, and returns `g_map_interaction_mode` to `1`. | Editor-mode shutdown. |
| `Read_Keyboard` | Trace string `Read_Keyboard`; game/map input dispatcher. Pressing `E/e` toggles `g_editor_mode_enabled`, calls `Edit_Start` when entering edit mode, and calls the editor-exit path when leaving. | Keyboard dispatcher, including editor toggle. |
| `CheckMouseOnWindow` | Trace string `CheckMouseOnWindow`; when no UI window consumes the mouse, editor mode `99` keeps hover/selection timing alive for map interaction. | Mouse-window hit test with editor-map fallback. |
| `Read_MLP_Edit` | Trace string `Read_MLP_Edit`; copies the full tile map into the editor backup at the start of a drag, then applies brush tools while the left mouse button is down. | Editor left-press/drag brush path. |
| `MLR_Edit_GameMap` | Trace string `MLR_Edit_GameMap`; editor left-click map handler. Tool cases create cities, fill city buildings, create armies, assign resource/feature ids, register two classes of named points, and batch-paint terrain. | Main editor map mutation path. |
| `Read_MRP_Edit` | Trace string `Read_MRP_Edit`; mirrors the backup-on-drag setup for right mouse input, then removes objects, armies, terrain overlays, resources, and ownership/visibility marks by tool mode. | Editor right-press/drag erase path. |
| `Read_MRR_Edit` | Trace string `Read_MRR_Edit`; editor right-click map handler. Opens linked objects, removes named-point links for tools `7/8`, or asks before deleting tile occupants. | Editor map removal/inspection path. |

### Editor-As-Semantics Probe

The built-in map editor is useful as a semantic oracle because it exposes the
same tables and tile fields that gameplay consumes. Editor setup functions bind
UI controls directly to definition tables such as `g_army_type_table`,
`g_ground_defs`, governments, buildings, sciences, and empire profiles; editor
map tools then mutate live `LandTile` and `ArmyUnit` records through the same
helpers used by normal gameplay. A productive recovery loop is therefore:

1. Recover editor-visible fields from the edit form bindings.
2. Follow those fields into gameplay predicates such as `Irrigate_Able`,
   `Resource_Able`, `Order_Check`, and `Do_Army_TurnJob`.
3. Name command/menu ids only when both the editor-facing data meaning and the
   runtime order behavior agree.

Current examples:

- Editor unit and terrain fields explain why `Order_Check` offers
  tile-improvement commands only for units whose type and current tile satisfy
  the same predicates used by the editor brush and turn-job completion chain.
- The ground brush writes `LandTile_0x100.terrain_kind`, resets the terrain
  layer/special flag, and then calls `Decode_NewMap`; that makes the editor a
  practical semantic oracle for the terrain visual fields later consumed by
  bridge checks, battle setup, and tile improvement completion.

### Editor Map Tool Modes

These are working meanings recovered from the mouse handlers, not confirmed
original enum names.

| Mode | Evidence | Working meaning |
|---:|---|---|
| `1` | `MLR_Edit_GameMap` creates a city and can fill all valid buildings; `Read_MRP_Edit` deletes a linked city/object after confirmation. | City/object tool. |
| `2` | `MLR_Edit_GameMap` validates `g_editor_selected_army_slot`, looks up `g_army_type_table`, and creates a map army; right-press removal deletes tile occupants. | Army/unit tool. |
| `3` | `Read_MLP_Edit` paints primary terrain kinds or road modes across the brush; `Read_MRP_Edit` removes road/terrain detail and decodes roads. | Ground/road brush. |
| `4` | Left-press writes random/selected battle resource ids at tile `+0x16`; right-press clears `+0x16`. | Battle resource/feature brush. |
| `5` | Left/right press edit fields `+0x13..+0x16`, `+0x24`, and alternate terrain around road/long-wall decode calls. | Overlay/road/long-wall detail brush. |
| `6` | `MLR_Edit_GameMap` assigns `g_editor_selected_city_resource_id` and initial stockpile; right-press clears tile `+0x17/+0xf8`. | City resource/feature brush. |
| `7` | Left-release adds a row in the large named-point table at `0x005e7d50`; right-release clears it. | Named point table A. |
| `8` | Left-release writes the secondary named-point table at `0x005e0050`; right-release clears it. | Named point table B. |
| `9` | Left-press paints tile owner/visibility for `g_editor_selected_country_id`; right-press clears the same owner/visibility bytes. | Ownership/visibility brush. |
| `0xb` | `MLR_Edit_GameMap` converts the cursor tile to diagonal coordinates, adds 27 template offsets from `g_editor_template_diag_offset_a/b`, converts back, and writes terrain/road template bytes. | Batch terrain-template brush. |

### Editor Terrain Template

Tool mode `0xb` applies a 27-tile stamp in a diagonal coordinate space. The
four helpers `Tile_To_DiagCoordA`, `Tile_To_DiagCoordB`,
`DiagCoords_To_TileX`, and `DiagCoords_To_TileY` convert between normal map
tile coordinates and this stamp-friendly coordinate pair. The template tables
at `g_editor_template_diag_offset_a/b` hold the per-entry diagonal offsets,
while `g_editor_template_terrain_kind` and `g_editor_template_road_mode` hold
the tile kind and road/detail mode to write before calling `Decode_NewMap`.

The same map-geometry cluster now includes broader runtime helpers:

- `Tile_Distance_With_Wrap` computes the hex/staggered-tile distance between
  two tile coordinates and can report when horizontal wrap adjusted the target
  x-coordinate.
- `Tile_Direction_DeltaX`, `Tile_Direction_DeltaY`, and `Mission_Direct`
  convert a target/source pair into an eight-way mission/facing direction used
  by AI and order setup.
- `Search_Round` walks the shared radius-offset buffers around the active army,
  calls `Search_Round_Candidate`, and publishes the best result through the
  `g_search_round_*` globals.
- `Game_Random_Mod` is the game's 15-bit LCG helper; map generation, diplomacy,
  city simulation, and battle code all use it for bounded random choices.

### `LandTile_0x100` Map Work Fields

The map editor is an unusually good semantic oracle here because the left-click
handler creates improvements, the right-click handler erases them, AI worker
code temporarily writes candidate values to evaluate yields, and the normal
turn loop advances the same fields to completion.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x19` | `Make_New_Work`, `Make_New_Make`, and `Clear_Forest_Or_Resource` reset it; `Do_Army_TurnJob` increments or decrements it against work thresholds before applying improvements/removals. | `tile_work_progress`. |
| `+0x1a` | `Read_MLP_Edit` overlay actions call `Make_New_Work(tile, 0..3)` after `Irrigate_Able`, `Pasturage_Able`, `Mine_Able`, or `Fish_Able`; `AI_Worker` writes the same values while scoring yields; `Read_MRP_Edit` clears it to `0xff`; `Order_Check` tests it to offer clear/cancel commands. | `tile_work_kind`: `0` irrigation/farmland, `1` pasture, `2` mine, `3` fishery, `-1` none. |
| `+0x1c` | `Make_New_Work` seeds irrigation/pasture countdowns from `DAT_0074a310/DAT_0074a311`; the first map scan in `Do_Army_TurnJob` decrements this field and clears `+0x19/+0x1a/+0x1c` when it expires. | `tile_work_expire_turns`. |
| `+0x20` | `Make_New_Work` stores `g_frame_tick` for newly applied visible work kinds; no gameplay caller found yet. | `tile_work_timestamp_tick`. |

The neighboring `+0x1d/+0x1e` bytes are probably visual/variant state for
improvements. Mine creation computes `+0x1d` from nearby terrain/height bytes
and randomness, while irrigation/pasture/fishery reset both bytes, but these
remain deliberately unnamed until more render/decode callers are tied down.

### `LandTile_0x100` Road, Bridge, And Long-Wall Fields

The road/bridge/long-wall overlay cluster is driven by the same edit and worker
paths as the work fields above, but final rendering state is recomputed from
neighboring tiles by the decode helpers.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x13` | `Read_MLP_Edit` and `Make_New_Make` seed this to `0` when placing road-like overlays; `Read_MRP_Edit` clears it to `-1`; `Decode_Road` recomputes the final connected road sprite id from neighboring `+0x13` roads and `+0x15` bridges. | `road_connection_tile_id`. |
| `+0x14` | Editor overlay kinds `0..2` are written here; the country/statistics pass counts roads by this byte when `+0x13` is present; worker action `0x15` checks for value `2` when completing/upgrading a road-like overlay. | `road_overlay_kind`. |
| `+0x15` | `Bridge_Able` requires this to be absent; bridge placement stores `Bridge_Able(tile) - 1`; `Decode_Road` treats nonnegative values as road connectors; bridge erase clears it together with road fields. | `bridge_variant_id`. |
| `+0x24` | `Make_New_Make(kind 4)` starts long-wall placement here and `Read_MRP_Edit` erases it; `Decode_LongWall` recomputes connected long-wall ids; `Map_To_Battle_Army` also reads its sign to select terrain-dependent versus doubled defense/support stat modifiers. | `long_wall_or_battle_bonus_mode`. |

`Decode_Road` and `Decode_LongWall` still show some raw `+0x13/+0x14/+0x24`
accesses because their local tile pointers decompile as `char *` or integer
addresses. The field names are nevertheless validated by the typed editor,
worker, predicate, and battle-conversion callers.

## Useful Offsets

### `MapScenarioInfo_0x16c`

`Before_Window_Edit_File_Detail` binds the editor-visible parts of this record,
while `Load_Map_GameInfo` preserves additional rule/state dwords from the map
file. Some late rule fields are therefore named from runtime use rather than
from an isolated editor label.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Editor label is file name; `Load_Map_GameInfo` copies the first short string here and the custom-map list formats it. | file name bytes. |
| `+0x11` | Editor label is author name; `Load_Map_GameInfo` copies the second string here. | author name bytes. |
| `+0x24` | Loader clears it when expanding older `0x168` records; edit detail startup also clears it. | editor scratch or unused field. |
| `+0x28` | Editor label is edit status; options are edit terrain, country setup, and normal mode. | edit status mode. |
| `+0x2c` | Editor label is game mode; options include open-world, China-closed, and random. | gameplay mode. |
| `+0x30` | Editor label is difficulty; diplomacy and map systems compare it against tier thresholds. | difficulty level. |
| `+0x34` | Third copied string in `Load_Map_GameInfo`. | subtitle or author bytes. |
| `+0x45` | Fourth copied string in `Load_Map_GameInfo`. | short description bytes. |
| `+0x58` | Editor label is player country. | player country id. |
| `+0x5c` | Editor label is current year; UI string setup formats this value. | current year. |
| `+0x60/+0x64` | Editor labels are country count and country limit; custom-map initialization clamps count against the limit. | country count / limit. |
| `+0x68` | Loader copies 22 dwords; custom-map selection uses this area while choosing active country setup. | country slot values. |
| `+0xc0` | Loaded rule/config dword; no editor label has been isolated yet. | scenario rule. |
| `+0xc4` | Editor label is density; options include near-player and random placement. | country density setting. |
| `+0xc8` | Editor label is country feature; options include original, random, and custom. | country feature setting. |
| `+0xcc/+0xd0` | Editor labels are disaster count/frequency and disaster limit. | disaster settings. |
| `+0xd4` | Editor label is barbarian setting; battle setup halves attack or defense stat groups depending on values `0` or `1`, and city-round logic has a special value `2` path. | barbarian setting. |
| `+0xd8` | Editor label is barbarian count. | barbarian count setting. |
| `+0xdc` | Editor label is resource setting; custom-map initialization sets it when country/template validation fails. | resource setting. |
| `+0xe0` | Editor label is specialty-product count. | special-product count setting. |
| `+0xe4` | Editor label is origin range error. | origin range error setting. |
| `+0xe8` | `Do_Map`, `Cal_City_Resource`, `City_Business`, `City_Building_AI`, and `Put_City_Make` gate city resource stockpiles, trade resources, and resource-dependent build paths on this value. | city resource system enabled. |
| `+0xec` | `City_Resource_Change` applies the government corruption deduction only when this value is zero. | corruption deduction mode. |
| `+0xf0..0xfc` | Loaded rule/config dwords; editor labels and direct runtime consumers have not been isolated yet. | scenario rule values. |
| `+0x100` | `Game_Frame_Pump` decrements it once per second and calls `Prepare_City_Doing` when automatic processing is enabled and the value reaches zero. | auto city processing countdown. |
| `+0x104` | `Load_Dat` and `MLR_Edit_SelCustomMap` branch on it before setting map dimensions. | map size mode. |
| `+0x108` | Editor label is science selection; options select one of five science tables. | science table choice. |
| `+0x10c` | `Load_Map_GameInfo` copies a 64-byte text field here. | long description bytes. |
| `+0x14c` | Editor label is wrap setting; map decode, road/long-wall decode, near-city scans, battle entry, and keyboard movement allow x wrapping when this is `1`. | horizontal wrap setting. |
| `+0x150` | Editor label is place-name setting; map editing checks it before named-point placement. | place-name setting. |
| `+0x154` | Late numeric value loaded from the scenario-info file; editor label has not been isolated yet. | scenario value. |
| `+0x158` | `MLR_Edit_SelCustomMap` takes a different initialization path when nonzero. | scripted start or generated flag. |
| `+0x15c/+0x160` | Late numeric values initialized by the detail form and read from the scenario-info file. | scenario values. |
| `+0x164` | Editor label is movement base; keyboard/map navigation uses it as a scroll or movement quantum. | movement base. |
| `+0x168` | Final byte copied from legacy scenario-info payloads. | scenario flag. |

### `LandTile_0x100`

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | `Read_MLP_Edit` writes `g_editor_selected_terrain_kind`; `Decode_NewMap` branches on normal terrain `0..10` and special terrain `0xb..0xe`; `Make_Battle_Map` uses it as the primary battle terrain source. | terrain kind. |
| `+0x02` | `Make_Battle_Map` uses this as a fallback when the primary tile kind is outside `0..10`. | alternate battle terrain kind. |
| `+0x04` | `Decode_NewMap` stores the resolved base terrain map-tile image id; `Bridge_Able` checks this sprite id against the bridge-capable range `0x1115..0x12c0`. | terrain sprite id. |
| `+0x06` | `Decode_NewMap` writes a sprite id for special terrain kinds `0xb..0xe`, based on the tile variant byte at `+0x03` and terrain class. | special terrain sprite id. |
| `+0x08` | The editor road/detail brush writes modes `3..5`, `Decode_NewMap` uses it to build hill/mountain/detail edge sprites, and battle setup changes stat modifiers when this signed value is positive, especially value `4`. | terrain detail or battle mode. |
| `+0x09..0x0e` | `Decode_NewMap` fills up to six terrain detail/edge sprite ids; `Clear_Mountain` resets the group to `-1`; mine completion scans the same bytes to choose a mine variant. | terrain detail sprite ids 0..5. |
| `+0x0f` | The editor writes `0` for normal terrain and `-1` for special terrain; long-wall decoding compares this byte as a layer/order value. | terrain layer or special flag. |
| `+0x10` | `load_dat.c` checks and counts. | city/land occupancy count or resource count. |
| `+0x12` | `city_round_check.c`, `near_beach_city_found.c`, `Bridge_Able`, `LongWall_Able`, and irrigation/worker paths treat this as a signed marker beside `+0x10`. | region / terrain / link marker. |
| `+0x13` | `Decode_Road` recomputes it from neighboring road and bridge markers; editor/right-click erase clears it to `-1`; road/rail placement seeds it at `0` before refresh. | road connection tile id. |
| `+0x14` | `Read_MLP_Edit` and `Make_New_Make` store editor overlay kinds `0..2`; road statistics count by this byte when `+0x13` is present; worker rail/road actions distinguish value `2`. | road overlay kind. |
| `+0x15` | `Bridge_Able` requires it to be `-1`; bridge placement stores `Bridge_Able(tile) - 1`; `Decode_Road` treats nonnegative bridge variants as road connectors; right-click bridge erase clears this with the road bytes. | bridge variant id. |
| `+0x16` | `Map_To_Battle_Army` indexes table `0x00589644` and adds battle stat bonuses when valid. | battle resource or feature id. |
| `+0x17` | `MLR_Edit_GameMap` tool `6` assigns this from the editor selector; `Do_Map` and `Calc_City_Resource` grow/consume the paired stockpile and clear the id at zero. | city resource or feature id. |
| `+0x24` | `Make_New_Make(kind 4)` seeds it for long-wall placement; `Decode_LongWall` recomputes connected long-wall ids; `LongWall_Able` requires `-1`; `Map_To_Battle_Army` also switches between terrain-dependent modifiers and doubled defense/support bonuses based on its sign. | long-wall connection / battle bonus mode. |
| `+0x25` | `City_Belong_Change` writes the new city owner here; near-city scans require it to match the active country. | tile owner/controller country id. |
| `+0x27` | `City_Belong_Change` writes the same new owner; `Diplomat_Allow` compares it with source/target ownership pairs. | secondary or previous owner country id. |
| `+0x28` | `load_dat.c` stores pointers indexed by `army_slot * 4`; city/battle scans now type these as `ArmyUnit_0x164_plus *`. | primary army pointer list. |
| `+0x50` | `load_dat.c` checks tile count/list. | army/unit count or city count. |
| `+0x54` | `load_dat.c` stores pointers indexed by slot; `City_Belong_Change` re-owns units from this list after capture. | secondary army pointer list. |
| `+0x7c` | `do_city.c`, `city_building.c`, and `city_people_change.c` add/check it beside the primary occupant count. | secondary occupant/defender count. |
| `+0x88` | `load_dat.c` dereferences during map repair. | linked record pointer or terrain object. |
| `+0xaa` | `City_Round_Check` compares this marker against `'('` while testing nearby tiles. | terrain or resource marker. |
| `+0xae` | `Load_Dat` rebuilds this from the large table at `0x005e7d50`; editor tool `7` creates it and `Read_MRR_Edit` clears it. | editor named point index A. |
| `+0xb0` | Editor tool `8` creates this from the secondary table at `0x005e0050`; `Read_MRR_Edit` clears it and resets the table row. | editor named point index B. |
| `+0xb3` | `City_Round_Check` tests this flag before allowing selected nearby-city actions. | city-round block flag. |
| `+0xb5..0xca` | `Diplomat_Allow`, `Do_Map`, `near_city_user_know_found`, and `user_set_city_resource` index by country id. | per-country visible/known flags. |
| `+0xcb..0xe0` | `City_Round_Check` tests `active_country + 0xcb` as a secondary exclusion/visibility gate. | per-country secondary visibility/exclusion flags. |
| `+0xf8` | Paired with `+0x17`; map and city resource ticks increase it up to a cap and city turns decrement it until the feature is exhausted. | city resource or feature stockpile. |

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
| `+0x26..+0x89` | `TestRoad` clears and fills 50 signed x coordinates. AI callers and `City_Round_Check` pass element 0 to `Add_OrderQueue_Army`; `Order_Go` shifts this array after each successful step. | queued path step x coordinates. |
| `+0x8a..+0xed` | Parallel 50-entry signed y coordinate array. `Apply_OrderQueue_Army` copies element 0 into render/animation coordinates for movement actions `0x24..0x27` and `0x40`. | queued path step y coordinates. |
| `+0xee..+0x11f` | `TestRoad` fills per-step bytes after spending `movement_points_remaining`; `Order_Go` decrements and shifts them while advancing through the route. | queued path step turn/cost bytes. |
| `+0x120` | Battle entry code tests this after movement/path scheduling before emitting animation records. | active animation step count. |
| `+0x121` | `TestRoad` increments it when a computed route does not end at the requested target; after repeated misses it compares the route endpoint with `+0x122/+0x124` and clears the route on regressions. | path replan/stall counter. |
| `+0x122/+0x124` | `TestRoad` records the current tile when starting a replan-stall sequence; `AI_UnClear` also seeds them before forcing a target direction. | path replan origin x/y. |
| `+0x127` | Near-city scans require zero for active/free units; diplomat order code sets it to nonzero. | mission state. |
| `+0x128` | Load/order paths test or write action ids such as `0x35`, `0x36`, `0x37`, and `0x39`. | mission/action id. |
| `+0x129` | Battle entry paths index direction tables `DAT_00589344`, `DAT_00589374`, and `DAT_005893b4` with this value to find the tile ahead. | facing or move direction. |
| `+0x12a` | Battle entry paths accumulate it by the turn/order delta and compare it with `ArmyTypeDef.mission_range_limit`, then reset it on action. | mission progress counter. |
| `+0x12c` | `Do_Army_TurnJob` refills it to `ArmyTypeDef.movement_or_speed * MapScenarioInfo.movement_base`; `TestRoad` spends it against terrain/road/overlay costs while building queued path steps. | movement points remaining. |
| `+0x12f` | `BattleArmy(..., unit->strength_or_health / 0xe + 1, ...)` derives formation count from it. | strength/health byte. |
| `+0x130` | Battle entry paths increment and reset it around repeated battle-entry/stat checks before raising veteran/power state. | battle entry retry counter. |
| `+0x131` | Battle stat adjustment shifts by this value in `Map_To_Battle_Army`. | veteran level / power shift. |
| `+0x134/+0x136/+0x138` | Loaded from army type tables and cached as short stats. | cached stat shorts. |
| `+0x13c` | `BattleArmy` copies this value into `BattleUnit_0x64.map_unit_extra_id`; death/effect records later reuse it. | map unit extra id. |
| `+0x144` | `JoinTo`, `BreakOut`, and `Apply_OrderQueue_Army` require null for direct units and set this to the immediate carrier/group when a unit is carried or merged. | transport parent pointer. |
| `+0x148` | `JoinTo` increments the target, `BreakOut` resets/deducts it, and `Order_Check` uses it to offer join/unload commands. | cargo/subunit count. |
| `+0x14c` | When the immediate parent is itself carried, join/breakout paths copy the root carrier link here; same-tile scans compare it against selected carrier units. | root transport/carrier link. |
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
| `+0x2c` | Compared with `ArmyTypeDef.battlefield_movement_frames`. | step frame. |
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
| `+0x00` | Editor label is image-file number; `Put_City_Make` and table/UI paths skip zero entries. | image resource id / enabled flag. |
| `+0x04` | Editor label is usage permission. | usage permission. |
| `+0x08` | `Before_Edit_Army` binds this early dword to an editable list-style control; gameplay use is not yet isolated. | editor-visible rank/group value. |
| `+0x0c` | Editor label is army type class; `BattleArmy`, `Map_To_Battle_Army`, near-city scans, and battle resolution compare values `0`, `1`, and `2`. | unit class/domain. |
| `+0x10` | Editor label is requisitioned population; `City_Building` subtracts this from city population when completing unit production, while some order paths reuse it as a land/name index. | conscripted population cost / related index. |
| `+0x14..0x1e` | Editor label is army type name; UI and messages format this text from `g_army_type_table + id * 0x400 + 0x14`. | name bytes. |
| `+0x2c` | `BattleArmy` copies it into battle record slot `0x16`. | battle sprite/effect id. |
| `+0x38` | `City_View` uses it to select the unit image. | city-view image id. |
| `+0x3c` | Battle action loops compare animation/action counters against it. | battle action frame count. |
| `+0x4c/+0x70` | Editor labels are walk flag two and attack flag two. | secondary walk/attack flags. |
| `+0x60` | `Load_Dat` validates mission `0x29` counter `ArmyUnit +0x12a` against it. | mission range limit. |
| `+0x90` | `Load_Dat` validates idle class-2 mission counter against it. | special mission range limit. |
| `+0xe8/+0xe9/+0xec` | Editor labels are walking sound, attack sound, and death sound; `Apply_OrderQueue_Army` plays the walking sound id for visible movement transitions when nonnegative. | sound ids. |
| `+0xf0` | Editor label is production cost; `City_Building` and `Put_City_Make` compare city build progress against it. | build cost. |
| `+0xf4` | Derived by `Load_Dat` from the magnitude of `build_cost`. | build cost digit count/display width. |
| `+0xf8/+0xfc/+0x100` | Editor label for the block is attack ability; `Map_To_Battle_Army`, `BattleArmy`, production UI, and city threat logic use these as primary combat numbers. | attack/combat stats A/B/C. |
| `+0x104/+0x108/+0x10c` | Editor label for the block is defense ability; `Map_To_Battle_Army` mirrors these into defensive/support stat arrays. | defense/support stats A/B/C. |
| `+0x110` | Editor label is movement ability; `Load_Dat` caches it into `ArmyUnit +0x138` after scaling, and UI displays it divided by 9. | movement/speed. |
| `+0x114/+0x118` | Editor labels are attack-nearest and attack-farthest preferences. | attack targeting preferences. |
| `+0x120` | Editor label is search range; battle AI compares range/rank counters with this value. | search range. |
| `+0x124` | Editor label is attack category; battle entry and unclear/offensive AI give special handling to values `1` and `2` when selecting or allowing defenders. | attack category. |
| `+0x128` | Editor label is bombard attack. | bombard attack setting. |
| `+0x12c` | Editor label is carrying quantity; transport validation in `Load_Dat`, `AI_Diplomat`, and `Map_To_Battle_Army` requires this to be nonzero for carriers. | transport capacity. |
| `+0x130/+0x134` | Editor label for `+0x130` is attack target; battle entry paths combine these flags with carried/subunit types and `transport_mask` when deciding defender interaction coverage. | attack target / battle entry capability flags. |
| `+0x138` | Load repair intersects this with carried-unit capability masks. | transport mask. |
| `+0x13c` | Editor label is merge type; `Order_Check`, `Order_Join_Sel`, `Order_Join_All`, and `AI_Army` require matching positive values before same-tile units can merge. | merge group type. |
| `+0x140/+0x144` | Near-city/air and transport checks compare capability bitmasks through these fields. | capability / transportable masks. |
| `+0x148` | Editor label is border influence; `Add_New_View`, `BreakOut`, `Army_Belong_Change`, and the order applier pass this as the visibility/zone mask when adding or removing unit vision. | border influence / visibility zone mask. |
| `+0x14c` | Editor label is mountain movement. | mountain movement mode. |
| `+0x160` | Editor label is battlefield movement; `Battle_AutoArrange` and `Do_Battle_Army_And_Battle_Die` compare step/action counters against it. | battlefield movement frame count. |
| `+0x164/+0x184` | `City_Belong_Change` adds/removes shorts from city protection/resource counters while units are stationed. | city support deltas. |
| `+0x1a4` | Editor label is production weight; `City_Building_AI` compares this value between candidate unit types to bias production choice. | production weight. |
| `+0x1a8/+0x1ac/+0x1b0` | Editor labels are retired soldier types 1..3. | retired army type ids. |
| `+0x1b4/+0x1b8` | Editor label is required building; `Put_City_Make` requires these buildings completed unless they are `-1`, with several special cases. | unit prerequisite buildings. |
| `+0x1bc` | Editor label is fuel storage. | fuel capacity. |
| `+0x1c0` | Editor label is long-wall movement. | long-wall movement mode. |
| `+0x1c8` | Editor label is capturable; option list distinguishes cannot be captured, capturable, and capture-only. | capture mode. |
| `+0x1cc` | Editor label is hunger/endurance turns; `Do_Army_TurnJob`, `City_Resource_Change`, and keyboard/UI display paths recharge or show `ArmyUnit +0x132` against this limit. | supply or hunger turn limit. |
| `+0x1d4` | Editor label is upgraded army type; battle entry paths pass it to the rank-up handler when a unit reaches veteran/power level `4`. | upgrade army type id. |
| `+0x1d8` | Editor label is submarine reconnaissance; special battle entry path for army type `0x29` tests this with defender tile visibility before allowing interaction. | submarine reconnaissance setting. |
| `+0x1dc` | Editor label is custom naming. | custom name mode. |
| `+0x1e0..0x1e6` | Editor label is default name. | default name bytes. |
| `+0x1e8/+0x1ec/+0x1f0` | Editor labels are repair ability, maximum repair, and repair speed. | repair settings. |
| `+0x1f4` | Editor label is merge/reorganize. | merge/reorganize mode. |
| `+0x1f8..` | `Put_City_Make` compares 40 resource slots against city/country resource availability. | resource cost by kind. |
| `+0x298/+0x29c` | Editor labels are attack speed and post-attack delay; `Do_Battle_Army_And_Battle_Die` compares battle counters against them. | attack speed / post-attack delay. |

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
| `+0x6a0..0x6a3` | `city_resource_change.c` compares/scales city economic and research deltas with these byte levels; `After_Edit_Country` normalizes `+0x6a1..0x6a3` until their sum is `10`. | resource/construction/research/tax efficiency levels. |
| `+0x6a4..0x713` | `city_resource_change.c`, `Before_Edit_Science_Set`, and `diplomat_steal_science.c` index words by science id; value `2` means completed. This typed prefix covers early entries, while several paths reach later science ids by raw country-base arithmetic. | per-country science status array prefix. |
| `+0x714` | Compared with `2` in city-event condition. | `country_state_mode`. |
| `+0x9c4` | `city_resource_change.c` uses this as the selected science id, indexes `g_science_defs`, and treats `-1` as no current research, which blocks construction-worker research allocation. | `current_research_science_id`. |
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

The building table is now mostly labeled from `Before_Edit_Build` editor control
bindings, then cross-checked against `City_Building`, `City_Build_AI_Build_Able`,
`City_Upgrade`, city resource changes, and the city/building tooltip in
`Put_City_View`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Editor option label is "usable"; build lists skip zero records. | `is_usable`. |
| `+0x04` | Editor option label is "building class"; placement and city-view paths also test it before allowing/displaying some map structures. | `building_class`. |
| `+0x08` | Editor option label is "build location". | `build_location_mode`. |
| `+0x0c` | `Put_City_View` indexes a short building-category label table with this value. | display category id. |
| `+0x10` | Editor option label is "science era". | `science_era_requirement`. |
| `+0x14` | Editor option label is "city style"; city people/resource change paths also use this offset as the scan anchor for a per-building value block. | `city_style_requirement`. |
| `+0x1c..0x2c` | `Before_Edit_Build` binds this as a 17-byte text field; city/building UI draws building names from it. | `name_bytes`. |
| `+0x30..0x47` | Editor exposes six early numeric requirements; build/resource logic indexes this block by government/profile mode. | per-government population requirement block. |
| `+0x44` | `City_Upgrade` copies this short into city map-object tile records for upgraded structures. | tile object variant id. |
| `+0x48` | Editor label is "upgrade building"; `City_Upgrade` follows this id when an old building unlocks/replaces another. | `upgrade_building_id`. |
| `+0x4c/+0x50` | Editor labels are "building length" and "building width"; placement and build AI multiply these values and compare map footprint. | `footprint_length_tiles`, `footprint_width_tiles`. |
| `+0x54` | Production compares city `build_progress` against this. | `build_cost`. |
| `+0x5c` | Editor label is "maintenance cost"; gameplay adds it to city `building_income_yield` on completion and subtracts it on removal. | `maintenance_cost_or_income_yield_delta`. |
| `+0x60/+0x64/+0x68/+0x6c` | Editor labels are loyalty, happiness, security, and commerce effects; shown in building tooltip and applied through city stat/resource changes. | `loyalty_effect`, `happiness_effect`, `security_effect`, `commerce_effect`. |
| `+0x74` | Editor option label is "effect range". | `effect_range_mode`. |
| `+0x78..0x97` | Indexed by current country/resource state when showing build cost/resource requirements. | `resource_cost_by_kind`. |
| `+0x98` | Editor label is "population limit"; displayed in tooltip and compared by AI/city checks. | `population_limit`. |
| `+0x9c` | Editor label is "required population"; displayed beside population/development text and checked before construction. | `required_population`. |
| `+0xa0` | Editor label is "condition building"; build AI requires this completed unless `-1`. | `prerequisite_building_id`. |
| `+0xa4` | Editor option label is "building direction". | `building_direction_mode`. |
| `+0xa8..0xdb` / `+0xdc..0xeb` | `City_Resource_Change` accumulates these effect blocks into per-turn city resource and late city-resource totals; the editor exposes the same dwords. | city resource effect blocks. |
| `+0xec` | Editor option label is "autonomy policy"; production acceleration branches compare policy ids `2`, `4`, `5`, `6`. | `autonomy_policy`. |
| `+0xf0` | Editor label is "income limit". | `income_limit`. |

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
| `+0x1c/+0x20` | Research availability checks these prerequisite science ids for completion or `-1`; `Science_Know_With_Prerequisites` walks them to grant the required chain. | prerequisite science ids. |
| `+0x24` | Compared against `current_research_progress`, added to a country accumulator when learned, and displayed by `Put_Edit_Science_Exp`. | `research_cost_or_score`. |
| `+0x28` | Used in research pacing and AI evaluation. | `era_or_group_id`. |
| `+0x2c..0x43` | `Science_Next` scans the first six `g_science_priority_target_ids` and adds these weights multiplied by 5000 when an unmet target science is found. | AI priority weight block A. |
| `+0x44..0x5b` | `Science_Next` scans the second six `g_science_priority_target_ids` and adds these weights multiplied by 5000 when an unmet target science is found. | AI priority weight block B. |
| `+0x60` | `Put_Edit_Science_Exp` displays a building name from `g_building_defs` when this id is nonnegative; `Science_Next` gives a small AI score bonus for nonnegative ids. | unlocked building id. |
| `+0x64/+0x68` | `Put_Edit_Science_Exp` displays army icons/names from `g_army_type_table` when these ids are nonnegative; `Science_Next` scores them from army stats. | unlocked army type ids. |
| `+0x6c/+0x70` | `Put_Edit_Science_Exp` displays special-project names from `g_special_project_defs` when these ids are nonnegative; `Science_Next` gives a small AI score bonus for nonnegative ids. | unlocked special-project ids. |

`Before_Edit_Science_Set` indexes the selected country's science status array at
`0x0073575c + country_id * 0xe68`. In the recovered paths seen so far, state
`2` means known/completed, state `3` means blocked by prerequisites, and states
`0`/`4` are treated by the editor as editable/unstarted-like states. State `1`
is collected by `Science_Next` as available/current research.

### `CountryProfileDef_0x7c`

`Load_Dat` reads/writes the whole static profile block as `0x3070` bytes. The
table editor calls around `0x0045ee10` expose many columns with base
`0x00596218` and stride `0x7c`; active countries reference rows through
`CountryState_0xe68 + 0x03`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00..0x10` | Editor label is person name; profile editor text column starts at `0x00596218 + row * 0x7c`. | person name bytes. |
| `+0x11..0x21` | Editor label is honorific/title name; `Before_Edit_Empire_Hero` binds this as a second 17-byte text column at `0x00596229 + row * 0x7c`. | honorific title bytes. |
| `+0x24` | Editor label is image-file type; options are no image, static image, and animation. `Load_Dat`, `Edit_Finish`, and custom-map selection require this to be nonnegative before loading/showing `DIP_%02d` resources. | portrait image mode. |
| `+0x28` | Editor label is image-file number; `Before_Edit_Empire_Hero`, `Load_Dat`, and `Edit_Finish` format `DIP_%02d.IMG`/`.IDI` resource names from this value. | portrait resource id. |
| `+0x2c` | Editor label is ambition to dominate. | domination ambition. |
| `+0x30` | Editor label is endurance under burden. | burden resilience. |
| `+0x34` | Editor label is honesty and trustworthiness. | honesty trustworthiness. |
| `+0x38` | Editor label is exploration spirit. | exploration spirit. |
| `+0x3c` | Editor label is science emphasis. | science priority. |
| `+0x40` | Editor label is economic talent; `City_Round_Check` subtracts this percent from city route/canal work costs. | engineering discount percent. |
| `+0x44..0x58` | `Before_Edit_Empire_Hero` binds this as a six-dword editor block at `0x0059625c + row * 0x7c`; no per-element labels have been isolated yet. | profile editor value block. |
| `+0x5c` | Editor label is culture emphasis. | culture priority. |
| `+0x60` | Editor label is popular-support emphasis. | popular-support priority. |
| `+0x74` | Editor label is diplomacy music. | diplomacy music id. |
| `+0x78` | Editor label is government preference; option list is built from government definitions. | preferred government id. |

### `EmpireCountryDef_0x200`

`Before_Edit_Empire_Country` reads and writes `EMPIRE.DAT` as a `0xc800`
byte block. Its editor controls use base `0x00589a18` and stride `0x200`,
so the table is 100 records. Custom-map selection and editor finish paths use
the first dword as an enabled gate, then use `+0x38` to reach
`g_country_profile_defs`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00` | Custom-map selection and editor finish require this value to be positive/nonzero. | enabled / selectable flag. |
| `+0x04..0x14` | Editor label is country name; order UI formats bytes from this column. | country name bytes. |
| `+0x15..0x25` | Editor label is capital name. | capital name bytes. |
| `+0x26..0x36` | Editor label is alliance name. | alliance name bytes. |
| `+0x38` | Editor label is leader/person; custom-map selection, diplomacy, and editor finish use this as an index into `g_country_profile_defs`. | country profile id. |
| `+0x3c` | Editor label is flag number. | flag resource id. |
| `+0x40/+0x44` | Editor labels are origin X/Y; custom-map selection validates them against map bounds and passability. | origin tile x/y. |
| `+0x58/+0x5c` | Editor labels are building style and settlement marker; `Load_UI_Dip_EMG` tests building-style values `1` and `3`. | building style / settlement marker ids. |
| `+0x60` | `City_Resource_Change` compares this against `ScienceDef_0x88.era_or_group_id` for research pacing. | favored science era/group. |
| `+0x80` | `Add_New_View` and `Del_Army_View` use this only in gameplay mode `1` to allow all, none, or one fixed rectangular map region. | scenario visibility region mode. |
| `+0x88` | `Diplomat_Turn` compares diplomacy affinity and turn counters against this leader/country parameter. | diplomacy affinity threshold. |
| `+0x8c` | `Diplomat_Turn` subtracts this value from pressure/caution thresholds. | diplomacy pressure threshold. |
| `+0x90` | `AI_Army` uses it as the random expedition/search radius around the active city when choosing a target tile. | AI expedition radius. |
| `+0x94/+0x98/+0x9c` | `City_Building` adds `value - 6` build progress for matching building categories or unit production when positive. | production/build bonuses. |
| `+0xb4/+0xb8` | `City_Building` applies the category-6 build bonus only when both fields are above the gate. | category-6 build bonus and gate. |
| `+0xcc` | `Diplomat_Battle_Back` passes this to the audio/theme switcher for the selected side before the diplomacy battle screen. | diplomacy battle music id. |
| `+0xd0..0xf7` | Editor label is special army type; the editor exposes ten paired entries with `+0xf8..0x11f`. | special army type ids. |
| `+0xf8..0x11f` | Editor label is required science; paired with each special army type id. | special-army required science ids. |
| `+0x120/+0x124/+0x128` | `MLP_Edit_Empire_Country` writes palette row ids from three vertical strips; `Edit_Finish` and `Load_Dat` combine these ids with diplomacy UI color/image tables. | diplomacy UI color layers. |

### `GovernmentDef_0x74`

`Load_Dat` copies a `0x3a0` byte static government table from the save/static
data stream into `0x00599288`. `Before_Edit_Goverment` exposes the same base
with stride `0x74`, so the table is 8 records. Active countries index it with
`CountryState_0xe68.government_or_ai_mode`.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x08` | Editor label is happiness effect; `City_Building` and `City_Resource_Change` add it to city happiness/stability. | happiness effect. |
| `+0x0c` | Editor label is public-security effect. | security effect. |
| `+0x10` | Editor label is commerce effect; `City_Business` multiplies inter-city yield by this value. | commerce effect. |
| `+0x14` | Editor label is corruption degree; `City_Resource_Change` uses it as a percent-like loss factor adjusted by safety and buildings. | corruption level. |
| `+0x18/+0x1c` | Editor labels are construction effect and production effect. | construction / production effects. |
| `+0x20` | Editor label is tax capacity; `City_Resource_Change` subtracts it from country resource-pressure level before applying stability effects. | tax capacity. |
| `+0x24` | Editor label is suppression-army count; AI and city stability use it as the desired minimum local garrison. | suppression army count. |
| `+0x28` | Editor label is anti-war army count; `City_Resource_Change` treats `-1` as a garrison bonus mode and positive values as an over-garrison threshold. | antiwar army count. |
| `+0x2c` | Editor label is homesick-army count; `City_Resource_Change` counts stationed units away from the city tile and penalizes excess. | homesick army count. |
| `+0x30` | Editor label is army burden count; city stability penalizes cities whose round/protection timer exceeds this threshold. | army burden count. |
| `+0x34` | Editor label is loyalty effect; army-turn ownership drift uses it as a per-turn loyalty gain. | loyalty effect. |
| `+0x38` | Editor label is city limit; `City_Building_AI` compares total force/unit count against this value before choosing a build branch. | city limit. |
| `+0x3c` | Editor label is unrest from recruiting soldiers. | recruitment unrest. |
| `+0x40..0x6b` | `City_Resource_Change` indexes this 11-dword block by country `research_efficiency_level`. | research efficiency modifiers. |
| `+0x6c/+0x70` | Editor labels are revolution turns and allowed unrest. | revolution turns / allowed unrest. |

### `GroundDef_0x24`

`Load_Dat` copies a `0x21c` byte static ground table into `0x00589428`.
`Before_Edit_Ground` backs up the same block and binds controls with stride
`0x24`, giving 15 records.

The editor-facing ground flags are consumed by the same map-improvement
predicates used by `Read_MLP_Edit`, `MLR_Edit_GameMap`, `Order_Check`, and
`AI_Worker`. `Irrigate_Able`, `Pasturage_Able`, `Mine_Able`, `Fish_Able`, and
`LongWall_Able` are low-byte boolean predicates; `Bridge_Able` is the notable
exception and returns a positive bridge/tile-object value when placement is
possible.

| Offset | Evidence | Working field |
|---:|---|---|
| `+0x00..0x04` | Editor label is terrain-surface name. | surface name bytes. |
| `+0x08` | Editor label is irrigation farmland; `Irrigate_Able` requires this to be nonzero. | irrigation farmland enabled. |
| `+0x0c` | Editor label is pasture/ranch; `Pasturage_Able` requires this to be nonzero. | pasture enabled. |
| `+0x10` | Editor label is maritime fishery; `Fish_Able` requires this to be nonzero. | fishery enabled. |
| `+0x14/+0x18/+0x1c/+0x20` | Editor labels are food, gold, energy, and hillside-food output. | terrain resource outputs. |

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

## Pixel And Color Tables

`Init_Surface_Pixel_State` asks DirectDraw for the active 16-bit pixel format
and `Init_Pixel_Format_Tables` derives channel masks, shifts, bit counts, and
RGB-to-pixel lookup tables from it. The renderer supports both 5-6-5 and 5-5-5
layouts, selected by `g_pixel_red_bits/g_pixel_green_bits/g_pixel_blue_bits`.

| Working name | Evidence | Meaning |
|---|---|---|
| `g_pixel_red_mask` / `g_pixel_green_mask` / `g_pixel_blue_mask` | Copied from the DirectDraw pixel-format fields at `+0x10/+0x14/+0x18` and used by pixel decode/blend helpers. | Active 16-bit RGB channel masks. |
| `g_pixel_red_shift` / `g_pixel_green_shift` / `g_pixel_blue_shift` | Counted from the low zero bits of each mask in `Init_Pixel_Format_Tables`. | Shift count for extracting/packing each channel. |
| `g_pixel_red_bits` / `g_pixel_green_bits` / `g_pixel_blue_bits` | Counted contiguous one bits in each mask; `Init_Surface_Pixel_State` branches on 5-6-5 vs 5-5-5. | Bit width for each RGB channel. |
| `g_rgb_to_pixel_tables` / `g_green_to_pixel_table` / `g_blue_to_pixel_table` | `Init_Pixel_Format_Tables` fills three 256-entry tables plus shifted variants, and UI color constants OR entries from these tables. | 8-bit RGB component to active 16-bit pixel lookup tables. |
| `g_alpha_blend_component_tables` | `Init_Surface_Pixel_State` allocates `0x30300` bytes and fills red/green/blue blend component tables for 257 alpha steps. | Component lookup tables for alpha/blend rendering. |
| `g_luminance_plus_table` / `g_luminance_minus_table` | `Init_Surface_Pixel_State` fills 65536-entry brighten/darken tables from active RGB masks. | One-step luminance adjustment tables. |
| `g_color_transform_tables` | `Load_EMG_Base` allocates 27 `0x20000` tables, loads/saves `C_TABLE.DAT`, and rebuilds each with `MakeColorTable`. | Cached per-pixel color transform tables. |
| `g_fade_color_tables` | `Load_EMG_Base` allocates 10 `0x20000` tables, loads/saves `F_TABLE.DAT`, and rebuilds them with `MakeFadeColorTable`. | Cached fade/dimming color tables. |
| `g_dark_table_buffer` | `Load_EMG_Base` allocates `0x1e0000`, loads/saves `D_TABLE.DAT`, and rebuilds it with `Build_Dark_Table`. | Fade-resource-derived dark/luminance lookup buffer. |

The color-table lifecycle is now recovered as a group:

- `Decode_Pixel16_RGB` extracts channel values from an active-format 16-bit pixel.
- `Pixel16_To_Luminance_Level` converts a 16-bit pixel to a small brightness bucket used by the dark table.
- `MakeColorTable` builds one of the 27 cached transform tables from hue/saturation/value-style adjustments.
- `MakeFadeColorTable` builds one of the 10 fade tables.
- `Build_Dark_Table_From_Fade_Frame` consumes decoded fade-frame pixel data and writes luminance levels into `g_dark_table_buffer`.
- `Build_Dark_Table` clears `g_dark_table_buffer` and processes 80 fade frames from the loaded `FADE.EMG` resource.
- `Load_EMG_Base` owns the cache-file path: `C_TABLE.DAT`, `F_TABLE.DAT`, and `D_TABLE.DAT` are read when valid and regenerated/written otherwise.
- `Set_Color` consumes the active RGB-to-pixel tables to populate UI and map
  color constants after DirectDraw pixel-format setup.
- `Free_Pixel_Format_Tables` releases the luminance, RGB-to-pixel, and alpha
  blend lookup tables allocated by `Init_Surface_Pixel_State`.

## Shutdown And Resource Lifetime

`ShutDown_Game` is the broad application teardown path. It first drains dynamic
game lists through `Clear_All_Memory`, then frees long-lived map/render buffers,
writes `CONFIG.DAT` and `KEYDEF.DAT`, closes indexed IMG handles, and releases
base EMG/XMG resources before shutting down the window/DirectDraw layer.

| Working name | Evidence | Meaning |
|---|---|---|
| `g_bestpath_temp_buffer` | Freed in `ShutDown_Game` with the debug label `BESTPATH PathTemp`. | Pathfinding scratch buffer. |
| `g_resource_score_buffer` | Freed as `res_score`; `UserSet_City_Resource` writes candidate score tuples into it. | Temporary city resource scoring buffer. |
| `g_land_record_buffers` | `ShutDown_Game` walks 22 pointers and frees each as `LandRec`. | Per-country or per-slot land-record buffers. |
| `g_minimap_buffer` | Freed with the `minimap` shutdown label. | Minimap backing buffer. |
| `g_edit_dest_round_buffers` | Two buffers freed as `DestRound_0/1`; map editor brush code indexes them by parity and reads x/y offset pairs. | Editor brush destination offset tables. |

`Free_EMG_Base` releases the long-lived UI/resource bank loaded around
`Load_EMG_Base`, including the flag IMG bank, base EMG resources, and XMG
resources. `Safe_FreeIMG` zeroes an IMG handle after calling the image-free
helper, and `CloseIndexIMG` closes indexed IMG slots and their index arrays.

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
  `Clear_Surface`, `Set_Draw_Clip_Rect`, `Format_Text`,
  `Init_Pixel_Format_Tables`, `MakeColorTable`, and
  `MakeFadeColorTable`.

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
- `game/process_command_line_args.c`, `game/app_winmain_entry.c`, and
  `game/init_setup.c`: startup path, `/EDIT` mode detection, editor resource
  loading, and initial screen-state selection.
- `game/app_frame_pump.c`, `game/game_frame_pump.c`,
  `extra/menu_editmenu_init.c`, `extra/put_sub_editmenu.c`,
  `extra/mlr_newedit.c`, `extra/menu_editmenu_quit.c`,
  `extra/mouse_on_edit_sel_custom_map.c`,
  `extra/mlr_edit_sel_custom_map.c`, `extra/playgame_init.c`,
  `extra/edit_start.c`, and
  `extra/edit_finish.c`, `extra/read_keyboard.c`,
  `extra/mlr_edit_gamemap.c`, and `extra/read_mrr_edit.c`: runtime path into
  map/editor mode, editor menu selection, custom-map loading/deletion, editor
  toggle, whole-map backup allocation, and the left/right-click editor map
  mutation paths.
- `ui/add_new_data_format.c`, `ui/node_insert_data_format.c`,
  `ui/node_delete_data_format.c`, `ui/del_data_format.c`,
  `ui/reflash_data_format.c`, `ui/check_press_data_format.c`,
  `editor/before_edit_army.c`, `editor/before_edit_build.c`,
  `editor/before_edit_empire_country.c`, `editor/before_edit_government.c`,
  `editor/before_edit_ground.c`, `editor/before_edit_empire_hero.c`, and
  `editor/put_edit_science_exp.c`:
  generic editor form binding plus unit/building/empire-country/government/
  ground/country-profile table setup, useful for recovering static data-table
  semantics from editor controls.
- `game/do_city.c`: per-turn city simulation and city AI/resource/job/event
  processing.
- `game/do_battle_army_and_die.c`: battle army update and death processing.
- `game/start_map_battle_from_army.c` and
  `extra/start_map_battle_from_tile.c`: map-to-battle entry points that seed
  battle tiles, collect participating armies, and call battle setup.
- `ui/main_menu_putscreen.c`: main menu visual composition and animation.
- `render/present_dirty_rects.c`: final dirty-rect surface present.
- `render/init_surface_pixel_state.c`, `render/init_pixel_format_tables.c`,
  `render/load_emg_base.c`, `render/make_color_table.c`,
  `render/make_fade_color_table.c`, `render/build_dark_table.c`, and
  `render/build_dark_table_from_fade_frame.c`: active 16-bit pixel format
  setup plus cached color/fade/dark lookup-table generation.

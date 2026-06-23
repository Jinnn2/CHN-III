# Symbol Map

This file tracks recovered global/static symbols. Names here should remain
evidence-based and may be refined as structs improve.

Naming convention:

- `g_`: global variable or global table.
- `s_`: static local/module static when provenance is known.
- `ptr_`: pointer variable.
- `tbl_`: table.
- `buf_`: buffer.
- `count_`: count.
- `idx_`: index.
- `flag_`: boolean or bit flag.

| Address | Name | Type | Size | Confidence | Used By |
|---|---|---|---:|---:|---|
| `0x0074a040` | `g_land_tiles` | `LandTile_0x100 *` | 4 | 85% | map decode, editor, `Load_Dat`, battle setup |
| `0x00588b84` | `g_map_width_tiles` | `int` | 4 | 85% | map bounds, editor brush, tile indexing |
| `0x00588b88` | `g_map_height_tiles` | `int` | 4 | 85% | map bounds, editor brush, tile indexing |
| `0x00588b8c` | `g_map_width_tiles_cached` | `int` | 4 | 65% | map coordinate/index helpers |
| `0x00588b90` | `g_map_half_height_tiles` | `int` | 4 | 65% | map coordinate/index helpers |
| `0x00755928` | `g_map_size_mode` | `int` | 4 | 80% | tile stride selection in map/editor paths |
| `0x00589374` | `g_hex_neighbor_delta_x_by_parity` | `int[16]` | 64 | 75% | road/long-wall decode, AI/pathing, editor erase |
| `0x005893b4` | `g_hex_neighbor_delta_y_by_parity` | `int[16]` | 64 | 75% | road/long-wall decode, AI/pathing, editor erase |
| `0x00589644` | `g_battle_feature_values` | `int[16]` | 64 | 75% | `Resource_Able`, `Clear_Forest_Or_Resource`, battle conversion |
| `0x005e0050` | `g_secondary_named_points` | `MapNamedPoint_0x20[1000]` | 32000 | 80% | `Load_Dat`, editor named-point tool 8, `NewLand_Name` |
| `0x005e7d50` | `g_primary_named_points` | `MapNamedPoint_0x20[4500]` | 144000 | 80% | `Load_Dat`, editor named-point tool 7, city-name matching |
| `0x007350b8` | `g_country_states` | `CountryState_0xe68[24]` | 88416 | 80% | country/city/AI/diplomacy |
| `0x00749a54` | `g_active_country_index` | `int` | 4 | 80% | turn logic, city/order paths |
| `0x0074c82c` | `g_human_country_index` | `int` | 4 | 80% | UI/visibility/minimap |
| `0x00748e04` | `g_active_country` | `CountryState_0xe68 *` | 4 | 80% | active-turn country logic |
| `0x00706948` | `g_city_turn_list_head` | `City_0x1b8_plus *` | 4 | 80% | `Do_City`, city turn traversal |
| `0x00749184` | `g_current_city` | `City_0x1b8_plus *` | 4 | 80% | city UI/update paths |
| `0x00755980` | `g_current_city_land_tile` | `LandTile_0x100 *` | 4 | 75% | city/map cross-links |
| `0x0074c81c` | `g_current_city_x` | `uint` | 4 | 70% | city/map UI |
| `0x0074c820` | `g_current_city_y` | `uint` | 4 | 70% | city/map UI |
| `0x005d9258` | `g_battle_grid_cells` | `BattleGridCell_0x2c[0x240]` | 25344 | 75% | battle map/grid setup and decode |
| `0x005dfe68` | `g_battle_unit_count_by_side` | `int[2]` | 8 | 75% | battle arrange/setup |
| `0x005dfe88` | `g_battle_unit_list_head_by_side` | `BattleUnit_0x64 *[2]` | 8 | 75% | battle units by side |
| `0x005dff90` | `g_ddraw` | `void *` | 4 | 75% | DirectDraw runtime |
| `0x005dff94` | `g_front_surface` | `void *` | 4 | 75% | present/render |
| `0x005dff98` | `g_back_surface` | `void *` | 4 | 75% | present/render/lock |
| `0x005dff9c` | `g_frame_one_second_elapsed` | `int/bool` | 4 | 75% | `App_Frame_Pump`, `Game_Frame_Pump` |
| `0x005dffa0` | `g_frame_elapsed_ms_accum` | `int` | 4 | 75% | `App_Frame_Pump`, `Game_Frame_Pump` |
| `0x005dffa4` | `g_frame_count_this_second` | `int` | 4 | 75% | `App_Frame_Pump`, `Game_Frame_Pump` |
| `0x005dffa8` | `g_frame_count_last_second` | `int` | 4 | 75% | `App_Frame_Pump`, `Game_Frame_Pump`, debug/status draw |
| `0x005dfed8` | `g_app_screen_state` | `int` | 4 | 80% | main loop dispatch, menu/game/editor transitions |
| `0x005dfedc` | `g_directdraw_ready` | `int` | 4 | 75% | message loop idle guard, present path |
| `0x005dfee0` | `g_main_window` | `HWND` | 4 | 80% | window creation, DirectDraw setup, input/font helpers |
| `0x005dff04` | `g_single_instance_mutex` | `HANDLE` | 4 | 70% | `App_WinMain_Entry` single-instance guard |
| `0x005dff8c` | `g_app_instance` | `HINSTANCE` | 4 | 70% | window creation, setup/resource helpers |
| `0x0075cf00` | `g_present_use_blt_mode` | `int` | 4 | 75% | startup window style and DirectDraw present mode |
| `0x0058940c` | `g_resolution_mode_index` | `int` | 4 | 80% | startup display mode selection and resolution changes |
| `0x00734c08` | `g_client_width` | `int` | 4 | 80% | viewport/window size |
| `0x00734c14` | `g_client_height` | `int` | 4 | 80% | viewport/window size |
| `0x0074a56c` | `g_startup_work_dir` | `char[]` | unknown | 70% | `Init_Working_Directories` source path |
| `0x0074c62c` | `g_map_data_dir` | `char[]` | unknown | 70% | exception-map checks and map data loads |
| `0x005997b8` | `g_building_defs` | `BuildingDef_0x200[]` | unknown | 75% | city build UI/AI, building editor |
| `0x005817a8` | `g_science_defs` | `ScienceDef_0x88[]` | unknown | 75% | science editor/research |
| `0x00581778` | `g_science_priority_target_ids` | `int[12]` | 48 | 75% | science priority editor and `Science_Next` |
| `0x005a80b0` | `g_city_resource_defs` | `CityResourceDef_0xd8[40]` | 8640 | 80% | resource placement, city resource calc |
| `0x00589a18` | `g_empire_country_defs` | `EmpireCountryDef_0x200[100]` | 51200 | 80% | country editor, custom-map setup |
| `0x00596218` | `g_country_profile_defs` | `CountryProfileDef_0x7c[100]` | 12400 | 75% | country profile/hero editor |
| `0x00599288` | `g_government_defs` | `GovernmentDef_0x74[8]` | 928 | 75% | government editor, country modifiers |
| `0x00589428` | `g_ground_defs` | `GroundDef_0x24[15]` | 540 | 80% | ground editor, terrain definitions |
| `0x005aa2c8` | `g_army_type_table` | `ArmyTypeDef_0x400[91]` | 93184 | 75% | army/unit definitions, AI, battle |
| `0x00588b80` | `g_request_redraw` | `byte` | 1 | 70% | map/render update requests |
| `0x0057e94c` | `g_editor_tool_mode` | `int` | 4 | 80% | editor input switch |
| `0x00755954` | `g_editor_mode_enabled` | `int` | 4 | 80% | `Read_Keyboard`, `Edit_Start`, `Edit_Finish`, map decode/editor paths |
| `0x00748f2e` | `g_input_current_key_word` | `uint16/int` | 2 | 70% | frame pumps, `Read_Keyboard`, dialogs, text entry |
| `0x00748f2f` | `g_input_current_key_char` | `byte` | 1 | 70% | `Read_Keyboard` direction-char dispatch |
| `0x00589408` | `g_input_direction_current` | `int` | 4 | 70% | `Read_Keyboard` map/cursor direction dispatch |
| `0x0057f25c` | `g_input_direction_last` | `int` | 4 | 70% | `Read_Keyboard` held-direction repeat timing |
| `0x005c7810` | `g_map_bookmark_tile_x_slots` | `int field, stride 0x10` | 4 each | 70% | `Load_Dat`, `Read_Keyboard` map bookmark save/jump |
| `0x005c7814` | `g_map_bookmark_tile_y_slots` | `int field, stride 0x10` | 4 each | 70% | `Load_Dat`, `Read_Keyboard` map bookmark save/jump |
| `0x005c7818` | `g_map_bookmark_unknown_slots` | `int field, stride 0x10` | 4 each | 55% | `Load_Dat`, `Read_Keyboard`; third per-slot bookmark field, meaning not verified |
| `0x0077b0ac` | `g_input_key_down_bitmap` | `byte[256]?` | 256 | 75% | `Input_On_KeyDown`, `Input_On_KeyUp`, `Input_Is_KeyDownOrModifier` |
| `0x0077c038` | `g_input_modifier_flags` | `byte/int` | 4 | 75% | input key handlers and modifier queries |
| `0x0077ab9c` | `g_input_key_event_code_ring` | `uint16[64]` | 128 | 75% | keyboard event queue |
| `0x0077af20` | `g_input_key_event_type_ring` | `byte[64]` | 64 | 75% | keyboard event queue |
| `0x0077af60` | `g_input_key_event_read_index` | `byte/int` | 4 | 75% | keyboard event queue |
| `0x0077a698` | `g_input_key_event_write_index` | `byte/int` | 4 | 70% | keyboard event queue |
| `0x00715da8` | `g_editor_brush_size_index` | `int` | 4 | 75% | editor brush radius |
| `0x0074a360` | `g_tile_radius_offset_counts` | `int[5]` | 20 | 70% | editor brush loops |
| `0x0074c830` | `g_edit_dest_round_buffers` | `void *[2]` | 8 | 70% | editor brush offset buffers |
| `0x00716104` | `g_editor_left_press_active` | `int` | 4 | 75% | `Read_MLP_Edit` |
| `0x00716108` | `g_editor_form_input_blocked` | `byte` | 1 | 70% | editor input gating |
| `0x00716124` | `g_editor_map_backup_state` | `int` | 4 | 75% | editor undo/transaction backup |
| `0x00715da4` | `g_editor_ground_edit_submode` | `int` | 4 | 75% | terrain vs road edit mode |
| `0x00715f70` | `g_editor_selected_terrain_kind` | `int` | 4 | 75% | ground brush |
| `0x00716110` | `g_editor_selected_road_mode` | `int` | 4 | 75% | road brush |
| `0x0057e988` | `g_editor_selected_battle_feature_set` | `int` | 4 | 75% | battle-resource/feature brush |
| `0x007157dc` | `g_editor_battle_feature_variant_mode` | `int` | 4 | 70% | battle-feature random variant |
| `0x0057ea88` | `g_editor_battle_feature_base_id_slots` | `byte[24]` | 24 | 70% | feature id base slots, indexed by set with 4-byte stride |
| `0x0057ea9c` | `g_editor_battle_feature_custom_base_id` | `byte` | 1 | 65% | custom/random feature id base |
| `0x0057e950` | `g_editor_overlay_action` | `int` | 4 | 70% | overlay/road/long-wall brush |
| `0x0057e954` | `g_editor_overlay_kind` | `int` | 4 | 70% | overlay/road/long-wall brush |
| `0x00716118` | `g_editor_selected_city_resource_id` | `int` | 4 | 75% | city-resource brush |
| `0x00572a90` | `g_editor_resource_initial_stockpile` | `int` | 4 | 70% | city-resource brush stockpile |
| `0x0057e994` | `g_editor_selected_country_id` | `int` | 4 | 75% | editor city/unit/ownership tools |
| `0x0057e998` | `g_editor_selected_army_group` | `int` | 4 | 70% | editor army creation |
| `0x0057e99c` | `g_editor_selected_army_slot` | `int` | 4 | 70% | editor army creation |
| `0x007558fc` | `g_frame_tick` | `int` | 4 | 65% | render/menu timing |
| `0x0074c0a0` | `g_menu_action_tick` | `int` | 4 | 65% | main menu timing |
| `0x00707f8c` | `g_menu_item_emg_resource` | `void *` | 4 | 75% | main menu resource |
| `0x0070805c` | `g_mainmenu_emg_resource` | `void *` | 4 | 75% | main menu resource |
| `0x00707f90` | `g_mainmenu_sprite_bank` | `void *` | 4 | 75% | main menu XMG/sprite bank |
| `0x00707f7c` | `g_mainmenu_selected_index` | `int` | 4 | 70% | main menu input/draw |
| `0x00771f34` | `g_draw_sprite_fn` | `void *` | 4 | 70% | EMG/XMG sprite draw dispatch |
| `0x0077b1b4` | `g_view_center_x` | `int` | 4 | 70% | viewport/menu/map center |
| `0x0077b1c8` | `g_view_center_y` | `int` | 4 | 70% | viewport/menu/map center |
| `0x00758544` | `g_data_format_list_head` | `DataFormatNode *` | 4 | 70% | UI/data-format linked list |
| `0x00758548` | `g_data_format_list_tail` | `DataFormatNode *` | 4 | 70% | UI/data-format linked list |

## Next Symbol Work

- Add unresolved render resource handles around `0x00758560..0x007585f0`
  once each EMG/XMG slot is mapped to a file name.
- Promote remaining `DAT_` map editor owner/visibility bytes only after tool
  mode `9` is traced.
- Keep guessed names conservative; prefer `unknown_*` fields inside structures
  until an editor label, file format, or caller proves semantics.

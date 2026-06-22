// Ghidra headless script for semantic renaming and first-pass type recovery.
// Run before GhidraExport.java:
// analyzeHeadless <project_dir> CHNIII -process China2EX_fontfix8.exe -noanalysis \
//   -scriptPath tools/reverse_probe -postScript GhidraSemanticAnnotate.java

import ghidra.app.cmd.function.ApplyFunctionSignatureCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.ArrayDataType;
import ghidra.program.model.data.ByteDataType;
import ghidra.program.model.data.CategoryPath;
import ghidra.program.model.data.CharDataType;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeConflictHandler;
import ghidra.program.model.data.DataTypeManager;
import ghidra.program.model.data.DoubleDataType;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.data.FunctionDefinitionDataType;
import ghidra.program.model.data.IntegerDataType;
import ghidra.program.model.data.PointerDataType;
import ghidra.program.model.data.ParameterDefinition;
import ghidra.program.model.data.ParameterDefinitionImpl;
import ghidra.program.model.data.ShortDataType;
import ghidra.program.model.data.StructureDataType;
import ghidra.program.model.data.TypedefDataType;
import ghidra.program.model.data.UnsignedIntegerDataType;
import ghidra.program.model.data.UnsignedShortDataType;
import ghidra.program.model.data.VoidDataType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

public class GhidraSemanticAnnotate extends GhidraScript {
    private DataTypeManager dtm;
    private CategoryPath cat;
    private StructureDataType landTile;
    private StructureDataType city;
    private StructureDataType country;
    private StructureDataType armyUnit;
    private StructureDataType armyTypeDef;
    private StructureDataType battleUnit;
    private StructureDataType battleGridCell;
    private StructureDataType tmgImage;
    private StructureDataType buildingDef;
    private StructureDataType specialProjectDef;
    private StructureDataType scienceDef;
    private StructureDataType countryProfileDef;
    private StructureDataType governmentDef;
    private StructureDataType groundDef;
    private StructureDataType empireCountryDef;
    private StructureDataType mapScenarioInfo;
    private StructureDataType dataFormat;

    private static class Rename {
        long va;
        String name;
        Rename(long va, String name) {
            this.va = va;
            this.name = name;
        }
    }

    private static class GlobalRename {
        long va;
        String name;
        DataType type;
        GlobalRename(long va, String name, DataType type) {
            this.va = va;
            this.name = name;
            this.type = type;
        }
    }

    @Override
    protected void run() throws Exception {
        dtm = currentProgram.getDataTypeManager();
        cat = new CategoryPath("/CHNIII");

        createRecoveredTypes();
        renameFunctions();
        renameGlobals();
        applySelectedSignatures();
    }

    private Address addr(long va) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
    }

    private void replaceAt(StructureDataType s, int offset, DataType type, int length, String name, String comment) {
        s.replaceAtOffset(offset, type, length, name, comment);
    }

    private StructureDataType fixedStruct(String name, int size) {
        StructureDataType s = new StructureDataType(cat, name, 0);
        s.add(new ArrayDataType(ByteDataType.dataType, size, 1), "raw", "unrecovered bytes");
        return s;
    }

    private DataType resolve(DataType type) {
        return dtm.addDataType(type, DataTypeConflictHandler.REPLACE_HANDLER);
    }

    private void createRecoveredTypes() {
        city = fixedStruct("City_0x1b8_plus", 0x1b8);

        armyUnit = fixedStruct("ArmyUnit_0x164_plus", 0x164);
        replaceAt(armyUnit, 0x00, ByteDataType.dataType, 1, "army_type_id",
            "indexes g_army_type_table in map/battle conversion and city capture logic");
        replaceAt(armyUnit, 0x01, ByteDataType.dataType, 1, "owner_country_id",
            "compared and rewritten when city/tile ownership changes");
        replaceAt(armyUnit, 0x02, ByteDataType.dataType, 1, "target_or_previous_owner_id",
            "Map_To_Battle_Army compares it with owner and battle-side country ids");
        replaceAt(armyUnit, 0x18, ByteDataType.dataType, 1, "battle_slot_or_category",
            "used as an index into battle-side presence arrays");
        replaceAt(armyUnit, 0x1a, ShortDataType.dataType, 2, "tile_x",
            "battle entry paths use it with tile_y to locate the current LandTile");
        replaceAt(armyUnit, 0x1c, ShortDataType.dataType, 2, "tile_y",
            "battle entry paths use it with tile_x to locate the current LandTile");
        replaceAt(armyUnit, 0x1e, ShortDataType.dataType, 2, "render_or_anim_x",
            "movement/battle entry code passes it to animation helpers after tile placement");
        replaceAt(armyUnit, 0x20, ShortDataType.dataType, 2, "render_or_anim_y",
            "movement/battle entry code passes it to animation helpers after tile placement");
        replaceAt(armyUnit, 0x22, ShortDataType.dataType, 2, "target_tile_x_or_anim_x",
            "battle entry code stores computed target/path coordinates here");
        replaceAt(armyUnit, 0x24, ShortDataType.dataType, 2, "target_tile_y_or_anim_y",
            "battle entry code stores computed target/path coordinates here");
        replaceAt(armyUnit, 0x120, ByteDataType.dataType, 1, "active_anim_step_count",
            "battle entry code tests it before scheduling movement/animation records");
        replaceAt(armyUnit, 0x127, ByteDataType.dataType, 1, "mission_state",
            "zero means active/free in city-nearby scans; diplomat orders set it nonzero");
        replaceAt(armyUnit, 0x128, ByteDataType.dataType, 1, "mission_action_id",
            "order routines write action ids such as 0x2e, 0x2f, 0x37, 0x38, and 0x39");
        replaceAt(armyUnit, 0x129, ByteDataType.dataType, 1, "facing_or_move_direction",
            "battle entry paths index direction tables to find the tile ahead");
        replaceAt(armyUnit, 0x12a, ByteDataType.dataType, 1, "mission_progress_counter",
            "battle entry paths accumulate this against ArmyType.mission_range_limit and then reset it");
        replaceAt(armyUnit, 0x12f, ByteDataType.dataType, 1, "strength_or_health",
            "Map_To_Battle_Army converts it to battle formation count with / 0xe + 1");
        replaceAt(armyUnit, 0x130, ByteDataType.dataType, 1, "battle_entry_retry_counter",
            "battle entry paths increment and reset it around repeated stat/entry checks");
        replaceAt(armyUnit, 0x131, ByteDataType.dataType, 1, "veteran_level_or_power_shift",
            "battle stat bonus shifts by this value");
        replaceAt(armyUnit, 0x134, ShortDataType.dataType, 2, "cached_stat_a",
            "cached short derived from army-type data");
        replaceAt(armyUnit, 0x136, ShortDataType.dataType, 2, "cached_stat_b",
            "cached short derived from army-type data");
        replaceAt(armyUnit, 0x138, ShortDataType.dataType, 2, "cached_stat_c",
            "cached short derived from army-type data");
        replaceAt(armyUnit, 0x13c, IntegerDataType.dataType, 4, "map_unit_extra_id",
            "BattleArmy copies this into BattleUnit.map_unit_extra_id for death/effect records");
        replaceAt(armyUnit, 0x144, new PointerDataType(armyUnit, dtm), 4, "transport_parent",
            "checked for direct units and dereferenced as another army unit");
        replaceAt(armyUnit, 0x148, ByteDataType.dataType, 1, "cargo_or_subunit_count",
            "near-city scans and Map_To_Battle_Army add one to this value for carried/sub units");
        replaceAt(armyUnit, 0x14c, new PointerDataType(armyUnit, dtm), 4, "transport_or_carrier_link",
            "inverse carrier link checked against current unit and carrier mission state");
        replaceAt(armyUnit, 0x152, ByteDataType.dataType, 1, "map_presence_or_cargo_state",
            "battle entry and tile scans require zero for directly present active units; startup code compares it against 3");
        replaceAt(armyUnit, 0x154, new PointerDataType(city, dtm), 4, "stationed_city",
            "City_Belong_Change assigns the city; Map_To_Battle_Army reads city building statuses through it");
        replaceAt(armyUnit, 0x160, new PointerDataType(armyUnit, dtm), 4, "next_army",
            "country army linked-list traversal");
        resolve(armyUnit);

        landTile = fixedStruct("LandTile_0x100", 0x100);
        replaceAt(landTile, 0x10, ShortDataType.dataType, 2, "linked_count_or_city_count",
            "load_dat checks this count before rebuilding map links");
        replaceAt(landTile, 0x02, ByteDataType.dataType, 1, "alternate_battle_terrain_kind",
            "Make_Battle_Map uses this as a fallback terrain kind when primary kind is outside 0..10");
        replaceAt(landTile, 0x08, ByteDataType.dataType, 1, "battle_stat_terrain_mode",
            "Map_To_Battle_Army changes stat modifiers when this signed terrain mode is positive or equals 4");
        replaceAt(landTile, 0x12, ByteDataType.dataType, 1, "region_or_terrain_marker_a",
            "signed marker used by city-round and near-city checks beside linked_count_or_city_count");
        replaceAt(landTile, 0x13, ByteDataType.dataType, 1, "region_or_terrain_marker_b",
            "second signed marker used by city-round and near-city checks");
        replaceAt(landTile, 0x16, ByteDataType.dataType, 1, "battle_resource_or_feature_id",
            "Map_To_Battle_Army indexes a feature table at 0x00589644 and adds stat bonuses when the value is valid");
        replaceAt(landTile, 0x17, ByteDataType.dataType, 1, "city_resource_or_feature_id",
            "editor tool 6 assigns this id; city resource code grows/consumes the paired stockpile and clears it at zero");
        replaceAt(landTile, 0x24, ByteDataType.dataType, 1, "battle_stat_bonus_mode",
            "Map_To_Battle_Army treats negative values as terrain-dependent modifiers and nonnegative values as doubled defense/support bonuses");
        replaceAt(landTile, 0x25, ByteDataType.dataType, 1, "tile_owner_country_id",
            "City_Belong_Change writes the new owner; near-city scans require active-country ownership");
        replaceAt(landTile, 0x27, ByteDataType.dataType, 1, "tile_secondary_owner_id",
            "City_Belong_Change writes the new owner; diplomacy checks compare source/target ownership pairs");
        replaceAt(landTile, 0x28, new ArrayDataType(new PointerDataType(armyUnit, dtm), 10, 4), 0x28,
            "army_or_city_ptrs_a", "pointer list rebuilt in load_dat");
        replaceAt(landTile, 0x50, ByteDataType.dataType, 1, "army_count_or_occupant_count",
            "checked before iterating tile occupants");
        replaceAt(landTile, 0x54, new ArrayDataType(new PointerDataType(armyUnit, dtm), 10, 4), 0x28,
            "army_or_city_ptrs_b", "secondary occupant pointer list");
        replaceAt(landTile, 0x7c, ByteDataType.dataType, 1, "secondary_occupant_count",
            "count-like field paired with army_count_or_occupant_count in city build/population checks");
        replaceAt(landTile, 0x88, new PointerDataType(VoidDataType.dataType, dtm), 4, "linked_record",
            "dereferenced during load-time repair");
        replaceAt(landTile, 0xaa, ByteDataType.dataType, 1, "terrain_or_resource_marker",
            "City_Round_Check compares this marker against '('");
        replaceAt(landTile, 0xae, ShortDataType.dataType, 2, "editor_named_point_index_a",
            "editor tool 7 and Load_Dat map this tile to the large name/x/y table at 0x005e7d50");
        replaceAt(landTile, 0xb0, ShortDataType.dataType, 2, "editor_named_point_index_b",
            "editor tool 8 maps this tile to the secondary name/x/y table at 0x005e0050 and right-click removal clears it");
        replaceAt(landTile, 0xb3, ByteDataType.dataType, 1, "city_round_block_flag",
            "blocks selected City_Round_Check actions when set");
        replaceAt(landTile, 0xb5, new ArrayDataType(ByteDataType.dataType, 22, 1), 0x16,
            "visible_by_country", "per-country map visibility/knowledge flags used by diplomacy, map, and city resource setup");
        replaceAt(landTile, 0xcb, new ArrayDataType(ByteDataType.dataType, 22, 1), 0x16,
            "secondary_visible_or_excluded_by_country", "per-country secondary visibility/exclusion flags tested by City_Round_Check");
        replaceAt(landTile, 0xf8, IntegerDataType.dataType, 4, "city_resource_or_feature_stockpile",
            "paired with city_resource_or_feature_id; Do_Map/Calc_City_Resource increase it and city turns consume it");
        resolve(landTile);

        mapScenarioInfo = fixedStruct("MapScenarioInfo_0x16c", 0x16c);
        replaceAt(mapScenarioInfo, 0x00, new ArrayDataType(CharDataType.dataType, 0x11, 1),
            0x11, "file_name_bytes", "editor label is file name; Load_Map_GameInfo copies the first string here");
        replaceAt(mapScenarioInfo, 0x11, new ArrayDataType(CharDataType.dataType, 0x17, 1),
            0x17, "author_name_bytes", "editor label is author name; Load_Map_GameInfo copies the second string here");
        replaceAt(mapScenarioInfo, 0x24, IntegerDataType.dataType, 4, "editor_scratch_or_unused",
            "Load_Map_GameInfo clears this field before storing numeric scenario metadata");
        replaceAt(mapScenarioInfo, 0x28, IntegerDataType.dataType, 4, "edit_status_mode",
            "editor label is edit status; options are edit terrain, country setup, and normal mode");
        replaceAt(mapScenarioInfo, 0x2c, IntegerDataType.dataType, 4, "gameplay_mode",
            "editor label is game mode; options include open-world, China-closed, and random");
        replaceAt(mapScenarioInfo, 0x30, IntegerDataType.dataType, 4, "difficulty_level",
            "editor label is difficulty; diplomacy and map systems compare it against tier thresholds");
        replaceAt(mapScenarioInfo, 0x34, new ArrayDataType(CharDataType.dataType, 0x11, 1),
            0x11, "subtitle_or_author_bytes", "Load_Map_GameInfo copies the third string here");
        replaceAt(mapScenarioInfo, 0x45, new ArrayDataType(CharDataType.dataType, 0x13, 1),
            0x13, "description_short_bytes", "Load_Map_GameInfo copies the fourth string here");
        replaceAt(mapScenarioInfo, 0x58, IntegerDataType.dataType, 4, "player_country_id",
            "editor label is player country");
        replaceAt(mapScenarioInfo, 0x5c, IntegerDataType.dataType, 4, "current_year",
            "editor label is current year; UI string setup formats this value");
        replaceAt(mapScenarioInfo, 0x60, IntegerDataType.dataType, 4, "country_count",
            "editor label is country count; custom-map initialization clamps it to the country limit");
        replaceAt(mapScenarioInfo, 0x64, IntegerDataType.dataType, 4, "country_limit",
            "editor label is country limit");
        replaceAt(mapScenarioInfo, 0x68, new ArrayDataType(IntegerDataType.dataType, 22, 4),
            0x58, "country_slot_values", "Load_Map_GameInfo copies 22 dwords; custom-map load uses them to seed selectable countries");
        replaceAt(mapScenarioInfo, 0xc0, IntegerDataType.dataType, 4, "scenario_rule_c0",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0xc4, IntegerDataType.dataType, 4, "country_density_setting",
            "editor label is density; options include near-player and random placement");
        replaceAt(mapScenarioInfo, 0xc8, IntegerDataType.dataType, 4, "country_feature_setting",
            "editor label is country feature; options include original, random, and custom");
        replaceAt(mapScenarioInfo, 0xcc, IntegerDataType.dataType, 4, "disaster_frequency_setting",
            "editor label is disaster count/frequency");
        replaceAt(mapScenarioInfo, 0xd0, IntegerDataType.dataType, 4, "disaster_limit_setting",
            "editor label is disaster limit");
        replaceAt(mapScenarioInfo, 0xd4, IntegerDataType.dataType, 4, "barbarian_setting",
            "editor label is barbarian setting; battle/city event paths compare values 0, 1, and 2");
        replaceAt(mapScenarioInfo, 0xd8, IntegerDataType.dataType, 4, "barbarian_count_setting",
            "editor label is barbarian count");
        replaceAt(mapScenarioInfo, 0xdc, IntegerDataType.dataType, 4, "resource_setting",
            "editor label is resource setting; custom-map initialization sets it when country/template validation fails");
        replaceAt(mapScenarioInfo, 0xe0, IntegerDataType.dataType, 4, "special_product_count_setting",
            "editor label is specialty-product count");
        replaceAt(mapScenarioInfo, 0xe4, IntegerDataType.dataType, 4, "origin_range_error_setting",
            "editor label is origin range error");
        replaceAt(mapScenarioInfo, 0xe8, IntegerDataType.dataType, 4, "scenario_rule_e8",
            "city resource/trade/resource-feature rule gate");
        replaceAt(mapScenarioInfo, 0xec, IntegerDataType.dataType, 4, "scenario_rule_ec",
            "city income/tax rule gate");
        replaceAt(mapScenarioInfo, 0xf0, IntegerDataType.dataType, 4, "scenario_rule_f0",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0xf4, IntegerDataType.dataType, 4, "scenario_rule_f4",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0xf8, IntegerDataType.dataType, 4, "scenario_rule_f8",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0xfc, IntegerDataType.dataType, 4, "scenario_rule_fc",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0x100, IntegerDataType.dataType, 4, "scenario_rule_100",
            "rule/config dword exposed in the edit-file-detail form");
        replaceAt(mapScenarioInfo, 0x104, IntegerDataType.dataType, 4, "map_size_mode",
            "custom-map loader sets g_map_size_mode from this field before sizing the tile map");
        replaceAt(mapScenarioInfo, 0x108, IntegerDataType.dataType, 4, "science_table_choice",
            "editor label is science selection; options choose one of five science tables");
        replaceAt(mapScenarioInfo, 0x10c, new ArrayDataType(CharDataType.dataType, 0x40, 1),
            0x40, "description_long_bytes", "Load_Map_GameInfo copies a 64-byte text field here");
        replaceAt(mapScenarioInfo, 0x14c, IntegerDataType.dataType, 4, "horizontal_wrap_setting",
            "editor label is wrap setting; map tile neighborhood and decode paths allow x wrapping when this field is 1");
        replaceAt(mapScenarioInfo, 0x150, IntegerDataType.dataType, 4, "place_name_setting",
            "editor label is place-name setting; map editing checks it before allowing named-point placement");
        replaceAt(mapScenarioInfo, 0x154, IntegerDataType.dataType, 4, "scenario_value_154",
            "late scenario metadata loaded from file");
        replaceAt(mapScenarioInfo, 0x158, IntegerDataType.dataType, 4, "scripted_start_or_generated_flag",
            "custom-map loader takes a distinct initialization path when this field is nonzero");
        replaceAt(mapScenarioInfo, 0x15c, IntegerDataType.dataType, 4, "scenario_value_15c",
            "late scenario metadata loaded from file");
        replaceAt(mapScenarioInfo, 0x160, IntegerDataType.dataType, 4, "scenario_value_160",
            "late scenario metadata loaded from file");
        replaceAt(mapScenarioInfo, 0x164, IntegerDataType.dataType, 4, "movement_base",
            "editor label is movement base; keyboard/map navigation uses it as a scroll or movement quantum");
        replaceAt(mapScenarioInfo, 0x168, ByteDataType.dataType, 1, "scenario_flag_168",
            "last byte copied by Load_Map_GameInfo from legacy scenario-info files");
        resolve(mapScenarioInfo);

        dataFormat = fixedStruct("DataFormat_0xc8", 0xc8);
        replaceAt(dataFormat, 0x00, IntegerDataType.dataType, 4, "control_type",
            "Add_New_DataFormat first argument; NodeInsert_DataFormat switches on it");
        replaceAt(dataFormat, 0x08, IntegerDataType.dataType, 4, "x",
            "control x coordinate passed by table/detail setup functions");
        replaceAt(dataFormat, 0x0c, IntegerDataType.dataType, 4, "y",
            "control y coordinate passed by table/detail setup functions");
        replaceAt(dataFormat, 0x10, new PointerDataType(CharDataType.dataType, dtm), 4, "label_text",
            "copied from the show-string argument when non-empty");
        replaceAt(dataFormat, 0x14, IntegerDataType.dataType, 4, "data_record_stride",
            "stored from the record stride argument");
        replaceAt(dataFormat, 0x18, new PointerDataType(VoidDataType.dataType, dtm), 4, "bound_data_base",
            "base pointer for the edited data field");
        replaceAt(dataFormat, 0x1c, IntegerDataType.dataType, 4, "data_record_delta",
            "record end pointer minus start pointer in Add_New_DataFormat");
        replaceAt(dataFormat, 0x20, new PointerDataType(VoidDataType.dataType, dtm), 4, "bound_data_end",
            "end/base pointer for the edited data range");
        replaceAt(dataFormat, 0x24, new PointerDataType(VoidDataType.dataType, dtm), 4, "row_index_source",
            "table row/index source used by table-edit callers");
        replaceAt(dataFormat, 0x28, new PointerDataType(VoidDataType.dataType, dtm), 4, "alternate_data_base",
            "alternate bound data pointer passed by callers");
        replaceAt(dataFormat, 0x34, IntegerDataType.dataType, 4, "value_width_or_option_count",
            "numeric width for integer controls or option-count input for list controls");
        replaceAt(dataFormat, 0x38, new PointerDataType(VoidDataType.dataType, dtm), 4, "option_texts",
            "NodeInsert_DataFormat walks null-terminated option text lists for list-like controls");
        replaceAt(dataFormat, 0x40, IntegerDataType.dataType, 4, "derived_option_count",
            "computed option count for list-like controls");
        replaceAt(dataFormat, 0x44, IntegerDataType.dataType, 4, "derived_option_label_width",
            "computed maximum option label width");
        replaceAt(dataFormat, 0x48, IntegerDataType.dataType, 4, "value_limit_or_rows",
            "limit/row-count field used by Add_New_DataFormat and NodeInsert_DataFormat");
        replaceAt(dataFormat, 0x74, IntegerDataType.dataType, 4, "visible_option_rows",
            "clamped visible row count for scrolling list controls");
        replaceAt(dataFormat, 0x90, ByteDataType.dataType, 1, "has_scrollbar",
            "set when the option list is longer than the visible row count");
        replaceAt(dataFormat, 0xa4, ByteDataType.dataType, 1, "extra_blank_option",
            "caller flag that adds one extra list row");
        replaceAt(dataFormat, 0xb8, new PointerDataType(VoidDataType.dataType, dtm), 4, "owner_window",
            "owner window/context pointer whose control count is incremented");
        replaceAt(dataFormat, 0xbc, new PointerDataType(dataFormat, dtm), 4, "prev_data_format",
            "previous node in the global data-format linked list");
        replaceAt(dataFormat, 0xc0, new PointerDataType(dataFormat, dtm), 4, "next_data_format",
            "next node in the global data-format linked list");
        resolve(dataFormat);

        replaceAt(city, 0x01, ByteDataType.dataType, 1, "owner_country_id",
            "city ownership; compared with active/human country and rewritten by City_Belong_Change");
        replaceAt(city, 0x03, new ArrayDataType(CharDataType.dataType, 0x13, 1), 0x13, "name_bytes",
            "city name string is passed from city + 3; ends before tile_x/tile_y fields");
        replaceAt(city, 0x16, UnsignedShortDataType.dataType, 2, "tile_x", "used to index LandTile array");
        replaceAt(city, 0x18, UnsignedShortDataType.dataType, 2, "tile_y", "used to index LandTile array");
        replaceAt(city, 0x20, ByteDataType.dataType, 1, "max_worker_slots", "denominator for worker allocation");
        replaceAt(city, 0x21, ByteDataType.dataType, 1, "city_type_or_terrain_class", "indexes city text/type tables");
        replaceAt(city, 0x22, ByteDataType.dataType, 1, "development_level", "compared with 5 in city turn logic");
        replaceAt(city, 0x24, IntegerDataType.dataType, 4, "stored_population_or_value", "used for collapse/score thresholds");
        replaceAt(city, 0x28, IntegerDataType.dataType, 4, "city_policy_mode", "switch in do_city");
        replaceAt(city, 0x2e, ByteDataType.dataType, 1, "owner_or_active_flag", "used as owner/category index");
        replaceAt(city, 0x30, IntegerDataType.dataType, 4, "growth_or_industry_score", "event threshold stat");
        replaceAt(city, 0x4c, IntegerDataType.dataType, 4, "business_score", "city business/economy threshold");
        replaceAt(city, 0x50, IntegerDataType.dataType, 4, "safety_score", "city safety/happiness threshold");
        replaceAt(city, 0x54, IntegerDataType.dataType, 4, "science_or_resource_score", "worker/resource threshold");
        replaceAt(city, 0x5c, ByteDataType.dataType, 1, "production_mode",
            "current build kind: 0=army, 1=building, 2=special project, 0xff=none");
        replaceAt(city, 0x5d, ByteDataType.dataType, 1, "forced_worker_mode", "controls worker reassignment");
        replaceAt(city, 0x60, IntegerDataType.dataType, 4, "build_progress",
            "accumulates until army/building/special-project cost is reached");
        replaceAt(city, 0x64, new ArrayDataType(ByteDataType.dataType, 0x41, 1), 0x41,
            "building_status", "per-building state bytes; 0=missing, 2=completed in city build logic");
        replaceAt(city, 0xa5, new ArrayDataType(ByteDataType.dataType, 0x19, 1), 0x19,
            "special_project_status", "per-special-project state bytes, completed through city building mode 2");
        replaceAt(city, 0xbe, ByteDataType.dataType, 1, "has_special_capability",
            "gates special building classes and special AI production branches");
        replaceAt(city, 0xc0, ShortDataType.dataType, 2, "upgrade_cost_base", "used in city upgrade cost");
        replaceAt(city, 0xc2, ShortDataType.dataType, 2, "policy_timer_or_progress", "compared with +0xd2");
        replaceAt(city, 0xc4, ShortDataType.dataType, 2, "base_income", "copied into turn income accumulator");
        replaceAt(city, 0xc6, ShortDataType.dataType, 2, "worker_reassign_percent", "scales worker reassignment");
        replaceAt(city, 0xcc, IntegerDataType.dataType, 4, "population_or_stockpile", "used as production/population threshold");
        replaceAt(city, 0xd0, ByteDataType.dataType, 1, "population_growth_clamped",
            "forces growth rate to 1.0 and is cleared when population hits capacity");
        replaceAt(city, 0xd1, ByteDataType.dataType, 1, "event_lock", "must be -1 for some random city events");
        replaceAt(city, 0xd2, UnsignedShortDataType.dataType, 2, "policy_target_or_required_progress",
            "paired with +0xc2");
        replaceAt(city, 0xd4, UnsignedShortDataType.dataType, 2, "building_income_yield",
            "increased/decreased by completed buildings and added during city resource change");
        replaceAt(city, 0xd6, ShortDataType.dataType, 2, "collapse_delay_or_army_count", "checked before empty city removal");
        replaceAt(city, 0xd8, new ArrayDataType(ShortDataType.dataType, 10, 2), 20,
            "build_queue_entries", "queued production entries; ranges select army/building/special-project mode");
        replaceAt(city, 0xec, new ArrayDataType(ByteDataType.dataType, 10, 1), 10,
            "build_queue_tile_x", "per-queued item x/slot byte passed to build placement helpers");
        replaceAt(city, 0xf6, new ArrayDataType(ByteDataType.dataType, 10, 1), 10,
            "build_queue_tile_y", "per-queued item y/slot byte passed to build placement helpers");
        replaceAt(city, 0x100, ByteDataType.dataType, 1, "has_build_queue", "gates City_Building");
        replaceAt(city, 0x102, ShortDataType.dataType, 2, "round_or_protection_timer", "checked against age/turn");
        replaceAt(city, 0x164, ByteDataType.dataType, 1, "disaster_lock_a", "blocks happiness/safety decay");
        replaceAt(city, 0x165, ByteDataType.dataType, 1, "disaster_lock_b", "blocks happiness/safety decay");
        replaceAt(city, 0x169, ByteDataType.dataType, 1, "unassigned_workers", "incremented/decremented by job allocation");
        replaceAt(city, 0x16a, ByteDataType.dataType, 1, "science_workers", "job allocation bucket");
        replaceAt(city, 0x16b, ByteDataType.dataType, 1, "safety_workers", "job allocation bucket");
        replaceAt(city, 0x16c, ByteDataType.dataType, 1, "business_workers", "job allocation bucket");
        replaceAt(city, 0x16d, ByteDataType.dataType, 1, "construction_workers", "job allocation bucket");
        replaceAt(city, 0x16e, ByteDataType.dataType, 1, "base_resource_delta", "copied into turn resource accumulator");
        replaceAt(city, 0x16f, ByteDataType.dataType, 1, "mixed_workers", "reassigned between business/safety buckets");
        replaceAt(city, 0x176, ByteDataType.dataType, 1, "trade_route_count",
            "number of city trade/road links iterated by City_Business and adjusted on owner change");
        replaceAt(city, 0x177, ByteDataType.dataType, 1, "forced_event_pending", "one-turn city event flag");
        replaceAt(city, 0x17e, UnsignedShortDataType.dataType, 2, "neighbor_city_pressure",
            "recomputed by City_Round_Check from nearby linked cities and used by city build AI");
        replaceAt(city, 0x180, ByteDataType.dataType, 1, "event_transition_pending",
            "cleared when City_Event_Happen changes city_policy_mode");
        replaceAt(city, 0x181, ByteDataType.dataType, 1, "uses_manual_resource_setup", "selects resource setup path");
        replaceAt(city, 0x182, ByteDataType.dataType, 1, "processed_this_turn", "prevents duplicate do_city processing");
        replaceAt(city, 0x183, new ArrayDataType(ByteDataType.dataType, 40, 1), 40,
            "trade_resource_state", "per-resource trade state shared between connected cities; value 2 means exportable");
        replaceAt(city, 0x1ab, ByteDataType.dataType, 1, "nearby_city_count_bucket",
            "density bucket derived by City_Round_Check and consumed by City_Building_AI");
        replaceAt(city, 0x1b4, new PointerDataType(city, dtm), 4, "next_city", "city linked-list pointer");
        resolve(city);

        country = fixedStruct("CountryState_0xe68", 0xe68);
        replaceAt(country, 0x00, ByteDataType.dataType, 1, "is_active", "checked before per-country loops");
        replaceAt(country, 0x01, ByteDataType.dataType, 1, "leader_or_country_id", "compared against literal 0x22");
        replaceAt(country, 0x03, ByteDataType.dataType, 1, "country_profile_id",
            "indexes the 0x7c-byte country profile/static modifiers table at 0x00596218");
        replaceAt(country, 0x04, new ArrayDataType(ByteDataType.dataType, 32, 1), 32, "name_bytes", "used in diplomacy text");
        replaceAt(country, 0x38, new PointerDataType(city, dtm), 4, "capital_city",
            "city building completion stores the current city here when founding/capital-class buildings finish");
        replaceAt(country, 0x3c, new ArrayDataType(CharDataType.dataType, 32, 1), 32, "capital_name_bytes",
            "copied from the capital/primary city name");
        replaceAt(country, 0x5e, ByteDataType.dataType, 1, "diplomacy_focus_country",
            "country id or -1 used by Diplomat_Turn as a preferred/locked diplomatic target");
        replaceAt(country, 0x5f, ByteDataType.dataType, 1, "diplomacy_focus_limit",
            "count-like limiter paired with diplomacy_focus_country");
        replaceAt(country, 0x60, IntegerDataType.dataType, 4, "government_or_ai_mode", "city event condition");
        replaceAt(country, 0x6c, ByteDataType.dataType, 1, "production_freeze_flag",
            "when positive, City_Building skips normal production progress");
        replaceAt(country, 0x78, ByteDataType.dataType, 1, "coastal_building_unlock_a",
            "gates building ids 0x0f/0x27 in build AI and resource change");
        replaceAt(country, 0x79, ByteDataType.dataType, 1, "coastal_building_unlock_b",
            "gates building ids 0x10/0x28 in build AI and resource change");
        replaceAt(country, 0x7a, ByteDataType.dataType, 1, "government_bonus_enabled",
            "extra resource/research branch when government_or_ai_mode is 3");
        replaceAt(country, 0x7b, ByteDataType.dataType, 1, "population_growth_policy",
            "switch input for City_People_Born_Rate");
        replaceAt(country, 0x7c, UnsignedShortDataType.dataType, 2, "owned_city_count",
            "used as divisor for per-city country pressure and diplomacy city-count checks");
        replaceAt(country, 0x1aa, UnsignedShortDataType.dataType, 2, "total_force_or_unit_count",
            "country-wide count used for treasury/building and diplomacy thresholds");
        replaceAt(country, 0x1ac, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_state_by_country", "per-country relation state; values 2..5 are treated as normal relations");
        replaceAt(country, 0x204, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_treaty_flags_a", "one of several per-country pact/permission flags checked by Diplomat_Turn");
        replaceAt(country, 0x25c, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "trade_agreement_flags", "value 1 allows city/resource trade with the target country");
        replaceAt(country, 0x2b4, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_treaty_flags_b", "one of several per-country pact/permission flags checked by Diplomat_Turn");
        replaceAt(country, 0x30c, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_blockade_or_truce_flags", "blocks some actions when set; checked beside diplomacy_state_by_country");
        replaceAt(country, 0x364, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "tribute_or_payment_by_country", "money transfer amount when diplomacy_state_by_country is 4");
        replaceAt(country, 0x3bc, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_affinity_by_country", "large positive score used in AI diplomacy decisions");
        replaceAt(country, 0x414, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_caution_by_country", "threshold score reduced or clamped during Diplomat_Turn");
        replaceAt(country, 0x46c, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "diplomacy_pressure_by_country", "pressure/hostility score compared against leader personality thresholds");
        replaceAt(country, 0x4c4, new ArrayDataType(ByteDataType.dataType, 22, 1), 0x16,
            "city_trade_enabled_by_country", "byte flags used when preparing city trade output");
        replaceAt(country, 0x4da, new ArrayDataType(ByteDataType.dataType, 22, 1), 0x16,
            "pending_diplomatic_action_by_country", "Diplomat_Turn writes action ids before starting diplomacy");
        replaceAt(country, 0x506, new ArrayDataType(ByteDataType.dataType, 22, 1), 0x16,
            "diplomacy_contact_cooldown_by_country", "small countdown/cooldown adjusted around diplomacy contact attempts");
        replaceAt(country, 0x51c, new ArrayDataType(UnsignedShortDataType.dataType, 22, 2), 0x2c,
            "diplomacy_turn_counter_by_country", "per-country counter incremented and thresholded in Diplomat_Turn");
        replaceAt(country, 0x688, DoubleDataType.dataType, 8, "science_budget_or_treasury", "used by city upgrade cost");
        replaceAt(country, 0x698, DoubleDataType.dataType, 8, "population_or_score_total", "increased when city removed");
        replaceAt(country, 0x63c, ByteDataType.dataType, 1, "special_rule_level", "city event condition");
        replaceAt(country, 0x6a0, ByteDataType.dataType, 1, "resource_pressure_level",
            "compared against government tables before city resource scoring");
        replaceAt(country, 0x6a1, ByteDataType.dataType, 1, "construction_efficiency_level",
            "scales construction/research production in City_Resource_Change; After_Edit_Country keeps 0x6a1..0x6a3 sum at 10");
        replaceAt(country, 0x6a2, ByteDataType.dataType, 1, "research_efficiency_level",
            "indexes government tables and scales research production; After_Edit_Country keeps 0x6a1..0x6a3 sum at 10");
        replaceAt(country, 0x6a3, ByteDataType.dataType, 1, "tax_efficiency_level",
            "combined with resource pressure for positive treasury delta display; After_Edit_Country keeps 0x6a1..0x6a3 sum at 10");
        replaceAt(country, 0x6a4, new ArrayDataType(IntegerDataType.dataType, 0x1c, 4), 0x70,
            "science_status", "per-science status words; value 2 means completed/unlocked");
        replaceAt(country, 0x714, IntegerDataType.dataType, 4, "country_state_mode", "city event condition");
        replaceAt(country, 0x9c4, ShortDataType.dataType, 2, "current_research_science_id",
            "current science id; -1 disables construction-worker research allocation");
        replaceAt(country, 0x9c8, IntegerDataType.dataType, 4, "current_research_progress",
            "increased by construction workers and reset after research completion");
        replaceAt(country, 0x9cc, IntegerDataType.dataType, 4, "lifetime_research_progress",
            "accumulates alongside current research progress");
        replaceAt(country, 0x9d4, new ArrayDataType(ByteDataType.dataType, 0x41, 1), 0x41,
            "available_building_flags", "per-building availability/unlock flags checked before city construction");
        replaceAt(country, 0xa15, new ArrayDataType(ByteDataType.dataType, 0x19, 1), 0x19,
            "available_special_project_flags", "per-special-project availability flags for city building mode 2");
        replaceAt(country, 0xa2e, ByteDataType.dataType, 1, "available_special_project_count",
            "count compared before special-project AI build selection");
        replaceAt(country, 0xa2f, new ArrayDataType(ByteDataType.dataType, 0x58, 1), 0x58,
            "trainable_army_flags", "per-army availability/buildability flags used by city army production AI");
        replaceAt(country, 0xa87, new ArrayDataType(ByteDataType.dataType, 0x19, 1), 0x19,
            "special_project_pending_counts", "per-special-project pending countdown/count cleared on completion");
        replaceAt(country, 0xaa0, ByteDataType.dataType, 1, "pending_special_project_count",
            "decremented when special project pending count reaches zero");
        replaceAt(country, 0xa82, ShortDataType.dataType, 2, "turn_timer", "decremented in do_city");
        replaceAt(country, 0xa86, ByteDataType.dataType, 1, "timer_state", "set when turn_timer expires");
        replaceAt(country, 0xe18, ByteDataType.dataType, 1, "upgrade_permission_level", "city upgrade gate");
        replaceAt(country, 0xe14, IntegerDataType.dataType, 4, "city_resource_carryover",
            "temporary city-resource accumulator consumed and cleared by City_Resource_Change");
        resolve(country);

        armyTypeDef = fixedStruct("ArmyTypeDef_0x400", 0x400);
        replaceAt(armyTypeDef, 0x00, IntegerDataType.dataType, 4, "image_resource_id_or_enabled",
            "editor label is image-file number; unit production UI skips rows where the first word is zero");
        replaceAt(armyTypeDef, 0x04, IntegerDataType.dataType, 4, "usage_permission",
            "editor label is usage permission");
        replaceAt(armyTypeDef, 0x08, IntegerDataType.dataType, 4, "editor_rank_or_group_value",
            "Before_Edit_Army binds this early dword to a list-style editor control");
        replaceAt(armyTypeDef, 0x0c, IntegerDataType.dataType, 4, "unit_class",
            "editor label is army type class; 0=land, 1=air/naval-like, 2=special/transport-like in battle and near-city logic");
        replaceAt(armyTypeDef, 0x10, IntegerDataType.dataType, 4, "conscripted_population_cost",
            "editor label is requisitioned population; City_Building subtracts this from city population when the unit is produced; some order paths reuse it as a land/name index");
        replaceAt(armyTypeDef, 0x14, new ArrayDataType(CharDataType.dataType, 0x0b, 1), 0x0b,
            "name_bytes", "editor label is army type name; UI and messages format this 11-byte text field");
        replaceAt(armyTypeDef, 0x2c, IntegerDataType.dataType, 4, "battle_sprite_or_effect_id",
            "BattleArmy copies this into battle unit slot 0x16");
        replaceAt(armyTypeDef, 0x38, IntegerDataType.dataType, 4, "city_view_image_id",
            "City_View scales this value to select the unit image");
        replaceAt(armyTypeDef, 0x3c, IntegerDataType.dataType, 4, "battle_action_frame_count",
            "battle movement/action loops compare their animation frame counter against it");
        replaceAt(armyTypeDef, 0x4c, ByteDataType.dataType, 1, "walk_flag_b",
            "editor label is walk flag two");
        replaceAt(armyTypeDef, 0x60, IntegerDataType.dataType, 4, "mission_range_limit",
            "Load_Dat validates mission counter 0x12a against it for mission 0x29");
        replaceAt(armyTypeDef, 0x70, ByteDataType.dataType, 1, "attack_flag_b",
            "editor label is attack flag two");
        replaceAt(armyTypeDef, 0x90, IntegerDataType.dataType, 4, "special_mission_range_limit",
            "Load_Dat validates type class 2 idle mission counter against it");
        replaceAt(armyTypeDef, 0xe8, ByteDataType.dataType, 1, "walk_sound_id",
            "editor label is walking sound; Apply_OrderQueue_Army plays this sound id for visible movement transitions when nonnegative");
        replaceAt(armyTypeDef, 0xe9, ByteDataType.dataType, 1, "attack_sound_id",
            "editor label is attack sound");
        replaceAt(armyTypeDef, 0xec, ByteDataType.dataType, 1, "death_sound_id",
            "editor label is death sound");
        replaceAt(armyTypeDef, 0xf0, IntegerDataType.dataType, 4, "build_cost",
            "editor label is production cost; city production and Put_City_Make compare build_progress against this cost");
        replaceAt(armyTypeDef, 0xf4, IntegerDataType.dataType, 4, "build_cost_digit_count",
            "Load_Dat derives this display helper from build_cost magnitude");
        replaceAt(armyTypeDef, 0xf8, IntegerDataType.dataType, 4, "attack_stat_a",
            "editor label is attack ability; Map_To_Battle_Army and BattleArmy use it as a primary combat stat");
        replaceAt(armyTypeDef, 0xfc, IntegerDataType.dataType, 4, "attack_stat_b",
            "Map_To_Battle_Army and BattleArmy use it as a second combat stat");
        replaceAt(armyTypeDef, 0x100, IntegerDataType.dataType, 4, "attack_stat_c",
            "Map_To_Battle_Army reads it through DAT_005aa3c8 offset");
        replaceAt(armyTypeDef, 0x104, IntegerDataType.dataType, 4, "defense_or_support_stat_a",
            "editor label is defense ability; Map_To_Battle_Army and production UI read it through DAT_005aa3cc offset");
        replaceAt(armyTypeDef, 0x108, IntegerDataType.dataType, 4, "defense_or_support_stat_b",
            "Map_To_Battle_Army reads it through DAT_005aa3d0 offset");
        replaceAt(armyTypeDef, 0x10c, IntegerDataType.dataType, 4, "defense_or_support_stat_c",
            "Map_To_Battle_Army reads it through DAT_005aa3d4 offset");
        replaceAt(armyTypeDef, 0x110, IntegerDataType.dataType, 4, "movement_or_speed",
            "editor label is movement ability; Load_Dat caches this divided/scaled value and battle arrangement compares it");
        replaceAt(armyTypeDef, 0x114, IntegerDataType.dataType, 4, "attack_nearest_preference",
            "editor label is attack nearest");
        replaceAt(armyTypeDef, 0x118, IntegerDataType.dataType, 4, "attack_farthest_preference",
            "editor label is attack farthest");
        replaceAt(armyTypeDef, 0x120, IntegerDataType.dataType, 4, "search_range",
            "editor label is search range; battle AI compares this field against action counters");
        replaceAt(armyTypeDef, 0x124, IntegerDataType.dataType, 4, "attack_category",
            "editor label is attack category; battle entry and AI target selection treat values 1 and 2 as special defender/priority classes");
        replaceAt(armyTypeDef, 0x128, IntegerDataType.dataType, 4, "bombard_attack_setting",
            "editor label is bombard attack");
        replaceAt(armyTypeDef, 0x12c, IntegerDataType.dataType, 4, "transport_capacity",
            "editor label is carrying quantity; AI diplomat and load repair check this when validating carried units");
        replaceAt(armyTypeDef, 0x130, IntegerDataType.dataType, 4, "attack_target_mask",
            "editor label is attack target; battle entry paths combine this with carried/subunit types when deciding defender interaction coverage");
        replaceAt(armyTypeDef, 0x134, IntegerDataType.dataType, 4, "battle_entry_capability_b",
            "battle entry paths combine this with carried/subunit types beside capability_a and transport_mask");
        replaceAt(armyTypeDef, 0x138, IntegerDataType.dataType, 4, "transport_mask",
            "load repair intersects this bitmask with carried unit capability masks");
        replaceAt(armyTypeDef, 0x13c, IntegerDataType.dataType, 4, "merge_group_type",
            "editor label is merge type; join/order handlers require matching positive values before merging same-tile units");
        replaceAt(armyTypeDef, 0x140, IntegerDataType.dataType, 4, "air_or_city_capability_mask",
            "near-city-with-air logic compares this with active unit capability masks");
        replaceAt(armyTypeDef, 0x144, IntegerDataType.dataType, 4, "transportable_mask",
            "AI diplomat checks parent transport capacity against this mask");
        replaceAt(armyTypeDef, 0x148, IntegerDataType.dataType, 4, "border_influence_or_visibility_mask",
            "editor label is border influence; Add_New_View and army ownership/visibility transitions use this as the zone mask argument");
        replaceAt(armyTypeDef, 0x14c, IntegerDataType.dataType, 4, "mountain_movement_mode",
            "editor label is mountain movement");
        replaceAt(armyTypeDef, 0x160, IntegerDataType.dataType, 4, "battlefield_movement_frames",
            "editor label is battlefield movement; battle animation and auto-arrange compare step/action counters against this field");
        replaceAt(armyTypeDef, 0x164, ShortDataType.dataType, 2, "city_support_delta_a",
            "City_Belong_Change adds/removes this short while units are stationed in a city");
        replaceAt(armyTypeDef, 0x184, ShortDataType.dataType, 2, "city_support_delta_b",
            "City_Belong_Change adds/removes this short while units are stationed in a city");
        replaceAt(armyTypeDef, 0x1a4, IntegerDataType.dataType, 4, "production_weight",
            "editor label is production weight; City_Building_AI compares this weight between candidate unit types when selecting production");
        replaceAt(armyTypeDef, 0x1a8, IntegerDataType.dataType, 4, "retired_army_type_id_a",
            "editor label is retired soldier type 1");
        replaceAt(armyTypeDef, 0x1ac, IntegerDataType.dataType, 4, "retired_army_type_id_b",
            "editor label is retired soldier type 2");
        replaceAt(armyTypeDef, 0x1b0, IntegerDataType.dataType, 4, "retired_army_type_id_c",
            "editor label is retired soldier type 3");
        replaceAt(armyTypeDef, 0x1b4, IntegerDataType.dataType, 4, "prerequisite_building_a",
            "editor label is required building; Put_City_Make requires this completed unless -1, with several special cases");
        replaceAt(armyTypeDef, 0x1b8, IntegerDataType.dataType, 4, "prerequisite_building_b",
            "second building prerequisite for unit production");
        replaceAt(armyTypeDef, 0x1bc, IntegerDataType.dataType, 4, "fuel_capacity",
            "editor label is fuel storage");
        replaceAt(armyTypeDef, 0x1c0, IntegerDataType.dataType, 4, "long_wall_movement_mode",
            "editor label is long-wall movement");
        replaceAt(armyTypeDef, 0x1c8, ByteDataType.dataType, 1, "capture_mode",
            "editor label is capturable; option list distinguishes cannot be captured, capturable, and capture-only");
        replaceAt(armyTypeDef, 0x1cc, IntegerDataType.dataType, 4, "supply_or_hunger_turn_limit",
            "editor label is hunger/endurance turns; Do_Army_TurnJob and city resource change recharge ArmyUnit +0x132 up to this limit");
        replaceAt(armyTypeDef, 0x1d4, IntegerDataType.dataType, 4, "upgrade_army_type_id",
            "editor label is upgraded army type; battle entry paths pass this to the rank-up handler when a unit reaches veteran/power level 4");
        replaceAt(armyTypeDef, 0x1d8, IntegerDataType.dataType, 4, "submarine_recon_setting",
            "editor label is submarine reconnaissance; special battle entry path for army type 0x29 tests this with defender tile visibility");
        replaceAt(armyTypeDef, 0x1dc, IntegerDataType.dataType, 4, "custom_name_mode",
            "editor label is custom naming");
        replaceAt(armyTypeDef, 0x1e0, new ArrayDataType(CharDataType.dataType, 7, 1), 7,
            "default_name_bytes", "editor label is default name");
        replaceAt(armyTypeDef, 0x1e8, IntegerDataType.dataType, 4, "repair_mode",
            "editor label is repair ability");
        replaceAt(armyTypeDef, 0x1ec, IntegerDataType.dataType, 4, "repair_maximum",
            "editor label is maximum repair");
        replaceAt(armyTypeDef, 0x1f0, IntegerDataType.dataType, 4, "repair_rate",
            "editor label is repair speed");
        replaceAt(armyTypeDef, 0x1f4, IntegerDataType.dataType, 4, "merge_reorganize_mode",
            "editor label is merge/reorganize");
        replaceAt(armyTypeDef, 0x1f8, new ArrayDataType(IntegerDataType.dataType, 40, 4), 0xa0,
            "resource_cost_by_kind", "Put_City_Make compares these against country/city resource availability");
        replaceAt(armyTypeDef, 0x298, IntegerDataType.dataType, 4, "attack_speed",
            "editor label is attack speed; Do_Battle_Army_And_Battle_Die compares a battle counter against this field");
        replaceAt(armyTypeDef, 0x29c, IntegerDataType.dataType, 4, "post_attack_delay",
            "editor label is post-attack delay; Do_Battle_Army_And_Battle_Die compares a battle counter against this field");
        replaceAt(armyTypeDef, 0x2c0, new ArrayDataType(IntegerDataType.dataType, 22, 4), 0x58,
            "country_or_profile_build_modifiers", "production UI reads this late per-country/profile block");
        resolve(armyTypeDef);

        battleUnit = fixedStruct("BattleUnit_0x64", 0x64);
        replaceAt(battleUnit, 0x00, IntegerDataType.dataType, 4, "battle_layer_or_unit_class_flag",
            "BattleArmy sets it from ArmyType.unit_class == 2; grid code uses zero as front-layer selector");
        replaceAt(battleUnit, 0x04, IntegerDataType.dataType, 4, "army_type_id",
            "indexes g_army_type_table throughout battle processing");
        replaceAt(battleUnit, 0x08, IntegerDataType.dataType, 4, "owner_country_id",
            "compared against opposing battle units");
        replaceAt(battleUnit, 0x0c, IntegerDataType.dataType, 4, "battle_side",
            "side index passed into BattleArmy and used for side-specific battle globals");
        replaceAt(battleUnit, 0x10, IntegerDataType.dataType, 4, "battle_x",
            "grid x coordinate, initialized to -1 and later placed into a 0x18-wide battle grid");
        replaceAt(battleUnit, 0x14, IntegerDataType.dataType, 4, "battle_y",
            "grid y coordinate, initialized to -1 and later placed into a 0x18-wide battle grid");
        replaceAt(battleUnit, 0x18, IntegerDataType.dataType, 4, "facing_or_direction",
            "BattleArmy initializes it from a side-specific direction table and movement uses it as a direction index");
        replaceAt(battleUnit, 0x1c, IntegerDataType.dataType, 4, "action_frame",
            "Do_Battle_Army_And_Battle_Die increments/resets it during action animation");
        replaceAt(battleUnit, 0x20, IntegerDataType.dataType, 4, "moving_or_animating",
            "nonzero branch advances battle position over action frames");
        replaceAt(battleUnit, 0x24, IntegerDataType.dataType, 4, "action_state",
            "battle AI selects action ids such as 0x24 and 0x29 here");
        replaceAt(battleUnit, 0x28, IntegerDataType.dataType, 4, "action_substate",
            "paired with action_state during attack/move decisions");
        replaceAt(battleUnit, 0x2c, IntegerDataType.dataType, 4, "step_frame",
            "incremented against ArmyType.battlefield_movement_frames");
        replaceAt(battleUnit, 0x30, IntegerDataType.dataType, 4, "strength_chunk",
            "BattleArmy fills it from map unit strength and caps each chunk at 100");
        replaceAt(battleUnit, 0x34, new ArrayDataType(IntegerDataType.dataType, 3, 4), 0x0c,
            "attack_stats", "copied from Map_To_Battle_Army stat_a vector");
        replaceAt(battleUnit, 0x40, new ArrayDataType(IntegerDataType.dataType, 3, 4), 0x0c,
            "defense_stats", "copied from Map_To_Battle_Army stat_b vector");
        replaceAt(battleUnit, 0x4c, IntegerDataType.dataType, 4, "source_battle_slot",
            "copied from ArmyUnit.battle_slot_or_category");
        replaceAt(battleUnit, 0x50, IntegerDataType.dataType, 4, "formation_index",
            "BattleArmy assigns the chunk index within a multi-formation map army");
        replaceAt(battleUnit, 0x54, IntegerDataType.dataType, 4, "map_unit_extra_id",
            "copied from ArmyUnit +0x13c into the battle record");
        replaceAt(battleUnit, 0x58, IntegerDataType.dataType, 4, "battle_sprite_or_effect_id",
            "copied from ArmyType.battle_sprite_or_effect_id");
        replaceAt(battleUnit, 0x5c, new PointerDataType(battleUnit, dtm), 4, "prev_or_aux_link",
            "zeroed by BattleArmy; nearby battle list maintenance touches this slot");
        replaceAt(battleUnit, 0x60, new PointerDataType(battleUnit, dtm), 4, "next_battle_unit",
            "Battle_AutoArrange and arrange UI traverse battle records through this pointer");
        resolve(battleUnit);

        battleGridCell = fixedStruct("BattleGridCell_0x30", 0x30);
        replaceAt(battleGridCell, 0x00, IntegerDataType.dataType, 4, "terrain_kind",
            "Make_Battle_Map writes terrain/class ids and Decode_Battle branches on this value");
        replaceAt(battleGridCell, 0x04, IntegerDataType.dataType, 4, "base_tile_image_index",
            "Decode_Battle stores the resolved base tile image index here");
        replaceAt(battleGridCell, 0x08, IntegerDataType.dataType, 4, "overlay_tile_image_index",
            "Decode_Battle stores overlay/transition tile indices for terrain classes 0xb..0xe");
        replaceAt(battleGridCell, 0x0c, IntegerDataType.dataType, 4, "terrain_variant",
            "Make_Battle_Map initializes it to -1 and then picks a random variant from terrain tables");
        replaceAt(battleGridCell, 0x10, IntegerDataType.dataType, 4, "battle_region_or_owner_marker",
            "Make_Battle_Map writes side/map-region markers beside terrain_kind");
        replaceAt(battleGridCell, 0x14, new PointerDataType(battleUnit, dtm), 4, "front_unit",
            "front-layer battle unit pointer placed and cleared by arrange/update code");
        replaceAt(battleGridCell, 0x18, new PointerDataType(battleUnit, dtm), 4, "front_aux_or_target_unit",
            "battle update uses this adjacent front-layer pointer while resolving attacks/effects");
        replaceAt(battleGridCell, 0x1c, new PointerDataType(battleUnit, dtm), 4, "back_unit",
            "back-layer battle unit pointer placed and cleared by arrange/update code");
        replaceAt(battleGridCell, 0x20, new PointerDataType(battleUnit, dtm), 4, "back_aux_or_target_unit",
            "battle update uses this adjacent back-layer pointer while resolving attacks/effects");
        replaceAt(battleGridCell, 0x24, new PointerDataType(VoidDataType.dataType, dtm), 4, "effect_or_projectile",
            "Do_Battle_Stone and battle update store transient effect/projectile pointers here");
        replaceAt(battleGridCell, 0x2c, IntegerDataType.dataType, 4, "update_marker",
            "battle update clears this late cell marker during action resolution");
        resolve(battleGridCell);

        tmgImage = fixedStruct("DecodedImageHeader", 4);
        replaceAt(tmgImage, 0x00, UnsignedShortDataType.dataType, 2, "width", "draw routine reads first word");
        replaceAt(tmgImage, 0x02, UnsignedShortDataType.dataType, 2, "height", "draw routine reads second word");
        resolve(tmgImage);

        buildingDef = fixedStruct("BuildingDef_0x200", 0x200);
        replaceAt(buildingDef, 0x00, IntegerDataType.dataType, 4, "is_usable",
            "Before_Edit_Build label: usable; build lists skip zero records");
        replaceAt(buildingDef, 0x04, IntegerDataType.dataType, 4, "building_class",
            "Before_Edit_Build label: building class; placement and city-view paths also use this as a map-structure gate");
        replaceAt(buildingDef, 0x08, IntegerDataType.dataType, 4, "build_location_mode",
            "Before_Edit_Build label: build location");
        replaceAt(buildingDef, 0x0c, IntegerDataType.dataType, 4, "display_category_id",
            "Put_City_View indexes a short category label table from this value");
        replaceAt(buildingDef, 0x10, IntegerDataType.dataType, 4, "science_era_requirement",
            "Before_Edit_Build label: science era");
        replaceAt(buildingDef, 0x14, IntegerDataType.dataType, 4, "city_style_requirement",
            "Before_Edit_Build label: city style; city people/resource loops use this field as the anchor for a scan");
        replaceAt(buildingDef, 0x1c, new ArrayDataType(ByteDataType.dataType, 0x11, 1), 0x11,
            "name_bytes", "Before_Edit_Build binds this as a 17-byte text field; city/building UI draws names from it");
        replaceAt(buildingDef, 0x30, new ArrayDataType(IntegerDataType.dataType, 6, 4), 0x18,
            "per_government_population_requirement", "build UI/editor expose six early numeric requirements indexed by government/profile mode");
        replaceAt(buildingDef, 0x44, ShortDataType.dataType, 2, "tile_object_variant_id",
            "City_Upgrade copies this into city map object/tile records for upgraded structures");
        replaceAt(buildingDef, 0x48, IntegerDataType.dataType, 4, "upgrade_building_id",
            "city upgrade follows this id when an older building becomes obsolete/upgraded");
        replaceAt(buildingDef, 0x4c, IntegerDataType.dataType, 4, "footprint_length_tiles",
            "Before_Edit_Build label: building length; placement and build AI multiply this by footprint_width_tiles");
        replaceAt(buildingDef, 0x50, IntegerDataType.dataType, 4, "footprint_width_tiles",
            "Before_Edit_Build label: building width; placement and build AI multiply this by footprint_length_tiles");
        replaceAt(buildingDef, 0x54, IntegerDataType.dataType, 4, "build_cost",
            "city production compares build_progress against this value");
        replaceAt(buildingDef, 0x5c, ShortDataType.dataType, 2, "maintenance_cost_or_income_yield_delta",
            "Before_Edit_Build label: maintenance cost; gameplay adds/subtracts it from City.building_income_yield");
        replaceAt(buildingDef, 0x60, IntegerDataType.dataType, 4, "loyalty_effect",
            "Before_Edit_Build label: loyalty effect; shown in the city/building tooltip");
        replaceAt(buildingDef, 0x64, IntegerDataType.dataType, 4, "happiness_effect",
            "Before_Edit_Build label: happiness effect; City_Happy_Change consumes this when construction completes");
        replaceAt(buildingDef, 0x68, IntegerDataType.dataType, 4, "security_effect",
            "Before_Edit_Build label: security effect; shown in the city/building tooltip");
        replaceAt(buildingDef, 0x6c, IntegerDataType.dataType, 4, "commerce_effect",
            "Before_Edit_Build label: commerce effect; shown in the city/building tooltip");
        replaceAt(buildingDef, 0x74, IntegerDataType.dataType, 4, "effect_range_mode",
            "Before_Edit_Build label: effect range");
        replaceAt(buildingDef, 0x78, new ArrayDataType(IntegerDataType.dataType, 8, 4), 0x20,
            "resource_cost_by_kind", "resource/material cost array indexed by current country/resource state");
        replaceAt(buildingDef, 0x98, IntegerDataType.dataType, 4, "population_limit",
            "Before_Edit_Build label: population limit; AI and UI compare this against city stored_population_or_value");
        replaceAt(buildingDef, 0x9c, IntegerDataType.dataType, 4, "required_population",
            "Before_Edit_Build label: required population; UI displays it beside city population/development text");
        replaceAt(buildingDef, 0xa0, IntegerDataType.dataType, 4, "prerequisite_building_id",
            "build AI requires this completed unless it is -1");
        replaceAt(buildingDef, 0xa4, IntegerDataType.dataType, 4, "building_direction_mode",
            "Before_Edit_Build label: building direction");
        replaceAt(buildingDef, 0xa8, new ArrayDataType(IntegerDataType.dataType, 13, 4), 0x34,
            "city_resource_effects_a", "City_Resource_Change accumulates this 13-dword block into per-turn city resource deltas");
        replaceAt(buildingDef, 0xdc, new ArrayDataType(IntegerDataType.dataType, 4, 4), 0x10,
            "city_resource_effects_b", "City_Resource_Change accumulates this follow-up effect block into late per-turn city resource totals");
        replaceAt(buildingDef, 0xec, IntegerDataType.dataType, 4, "autonomy_policy",
            "Before_Edit_Build label: autonomy policy; production acceleration branches compare values such as 2, 4, 5, and 6");
        replaceAt(buildingDef, 0xf0, IntegerDataType.dataType, 4, "income_limit",
            "Before_Edit_Build label: income limit");
        resolve(buildingDef);

        specialProjectDef = fixedStruct("SpecialProjectDef_0x200", 0x200);
        replaceAt(specialProjectDef, 0x00, new ArrayDataType(ByteDataType.dataType, 56, 1), 56,
            "name_bytes", "project name is formatted from table base + project_id * 0x200");
        replaceAt(specialProjectDef, 0x38, IntegerDataType.dataType, 4, "build_cost",
            "city production compares build_progress against this value");
        replaceAt(specialProjectDef, 0x40, ShortDataType.dataType, 2, "income_yield_delta",
            "added to City.building_income_yield when completed");
        replaceAt(specialProjectDef, 0x48, IntegerDataType.dataType, 4, "global_effect_or_score_delta",
            "city resource change applies this when the owner matches");
        replaceAt(specialProjectDef, 0xd4, IntegerDataType.dataType, 4, "availability_or_display_flag",
            "edited in build table UI and checked by special-project logic");
        resolve(specialProjectDef);

        scienceDef = fixedStruct("ScienceDef_0x88", 0x88);
        replaceAt(scienceDef, 0x00, IntegerDataType.dataType, 4, "is_enabled",
            "research lists skip entries where this is zero");
        replaceAt(scienceDef, 0x04, new ArrayDataType(ByteDataType.dataType, 32, 1), 32,
            "name_bytes", "research completion and diplomacy messages format this text");
        replaceAt(scienceDef, 0x1c, IntegerDataType.dataType, 4, "prerequisite_science_a",
            "research is available when this science is completed or -1");
        replaceAt(scienceDef, 0x20, IntegerDataType.dataType, 4, "prerequisite_science_b",
            "second science prerequisite");
        replaceAt(scienceDef, 0x24, IntegerDataType.dataType, 4, "research_cost_or_score",
            "compared against current_research_progress and displayed by Put_Edit_Science_Exp");
        replaceAt(scienceDef, 0x28, IntegerDataType.dataType, 4, "era_or_group_id",
            "used in research pacing and AI evaluation");
        replaceAt(scienceDef, 0x2c, new ArrayDataType(IntegerDataType.dataType, 6, 4), 0x18,
            "ai_priority_weights_a",
            "Science_Next multiplies this six-dword block by 5000 using the first science priority target table");
        replaceAt(scienceDef, 0x44, new ArrayDataType(IntegerDataType.dataType, 6, 4), 0x18,
            "ai_priority_weights_b",
            "Science_Next multiplies this six-dword block by 5000 using the second science priority target table");
        replaceAt(scienceDef, 0x60, IntegerDataType.dataType, 4, "unlock_building_id",
            "Put_Edit_Science_Exp displays the building name when this id is nonnegative");
        replaceAt(scienceDef, 0x64, IntegerDataType.dataType, 4, "unlock_army_type_id_a",
            "Put_Edit_Science_Exp displays the army icon/name when this id is nonnegative");
        replaceAt(scienceDef, 0x68, IntegerDataType.dataType, 4, "unlock_army_type_id_b",
            "Put_Edit_Science_Exp displays a second army icon/name when this id is nonnegative");
        replaceAt(scienceDef, 0x6c, IntegerDataType.dataType, 4, "unlock_special_project_id_a",
            "Put_Edit_Science_Exp displays a special-project name when this id is nonnegative");
        replaceAt(scienceDef, 0x70, IntegerDataType.dataType, 4, "unlock_special_project_id_b",
            "Put_Edit_Science_Exp displays a second special-project name when this id is nonnegative");
        resolve(scienceDef);

        countryProfileDef = fixedStruct("CountryProfileDef_0x7c", 0x7c);
        replaceAt(countryProfileDef, 0x00, new ArrayDataType(CharDataType.dataType, 17, 1), 17,
            "person_name_bytes", "editor label is person name; profile/editor table text column starts at 0x00596218");
        replaceAt(countryProfileDef, 0x11, new ArrayDataType(CharDataType.dataType, 17, 1), 17,
            "honorific_title_bytes", "editor label is honorific/title name; profile/editor table text column starts at 0x00596229");
        replaceAt(countryProfileDef, 0x24, IntegerDataType.dataType, 4, "portrait_image_mode",
            "editor label is image-file type; options are no image, static image, and animation");
        replaceAt(countryProfileDef, 0x28, IntegerDataType.dataType, 4, "portrait_resource_id",
            "Before_Edit_Empire_Hero formats DIP_%02d IMG/IDI names from this paired resource id");
        replaceAt(countryProfileDef, 0x2c, IntegerDataType.dataType, 4, "domination_ambition",
            "editor label is ambition to dominate");
        replaceAt(countryProfileDef, 0x30, IntegerDataType.dataType, 4, "burden_resilience",
            "editor label is endurance under burden");
        replaceAt(countryProfileDef, 0x34, IntegerDataType.dataType, 4, "honesty_trustworthiness",
            "editor label is honesty and trustworthiness");
        replaceAt(countryProfileDef, 0x38, IntegerDataType.dataType, 4, "exploration_spirit",
            "editor label is exploration spirit");
        replaceAt(countryProfileDef, 0x3c, IntegerDataType.dataType, 4, "science_priority",
            "editor label is science emphasis");
        replaceAt(countryProfileDef, 0x40, IntegerDataType.dataType, 4, "engineering_discount_percent",
            "editor label is economic talent; city round/civil works cost subtracts this percent from route/canal costs");
        replaceAt(countryProfileDef, 0x44, new ArrayDataType(IntegerDataType.dataType, 6, 4), 0x18,
            "profile_editor_value_block_44", "Before_Edit_Empire_Hero binds this as a six-dword editor block");
        replaceAt(countryProfileDef, 0x5c, IntegerDataType.dataType, 4, "culture_priority",
            "editor label is culture emphasis");
        replaceAt(countryProfileDef, 0x60, IntegerDataType.dataType, 4, "popular_support_priority",
            "editor label is popular-support emphasis");
        replaceAt(countryProfileDef, 0x74, IntegerDataType.dataType, 4, "diplomacy_music_id",
            "editor label is diplomacy music");
        replaceAt(countryProfileDef, 0x78, IntegerDataType.dataType, 4, "preferred_government_id",
            "editor label is government preference; option list is built from government definitions");
        resolve(countryProfileDef);

        governmentDef = fixedStruct("GovernmentDef_0x74", 0x74);
        replaceAt(governmentDef, 0x08, IntegerDataType.dataType, 4, "happiness_effect",
            "editor label is happiness effect; city building/resource paths add it to happiness/stability");
        replaceAt(governmentDef, 0x0c, IntegerDataType.dataType, 4, "security_effect",
            "editor label is public-security effect");
        replaceAt(governmentDef, 0x10, IntegerDataType.dataType, 4, "commerce_effect",
            "editor label is commerce effect; City_Business multiplies inter-city yield by this factor");
        replaceAt(governmentDef, 0x14, IntegerDataType.dataType, 4, "corruption_level",
            "editor label is corruption degree; City_Resource_Change uses it as a percent-like loss factor adjusted by safety/buildings");
        replaceAt(governmentDef, 0x18, IntegerDataType.dataType, 4, "construction_effect",
            "editor label is construction effect");
        replaceAt(governmentDef, 0x1c, IntegerDataType.dataType, 4, "production_effect",
            "editor label is production effect");
        replaceAt(governmentDef, 0x20, IntegerDataType.dataType, 4, "tax_capacity",
            "editor label is tax capacity; City_Resource_Change subtracts it from country resource_pressure_level before applying stability effects");
        replaceAt(governmentDef, 0x24, IntegerDataType.dataType, 4, "suppression_army_count",
            "editor label is suppression-army count; AI and city stability use it as the desired minimum local garrison");
        replaceAt(governmentDef, 0x28, IntegerDataType.dataType, 4, "antiwar_army_count",
            "editor label is anti-war army count; -1 enables a garrison happiness bonus and positive values cap local occupants");
        replaceAt(governmentDef, 0x2c, IntegerDataType.dataType, 4, "homesick_army_count",
            "editor label is homesick-army count; stationed units away from the city are penalized beyond this limit");
        replaceAt(governmentDef, 0x30, IntegerDataType.dataType, 4, "army_burden_count",
            "editor label is army burden count; city stability penalizes cities above this round/protection unit threshold");
        replaceAt(governmentDef, 0x34, IntegerDataType.dataType, 4, "loyalty_effect",
            "editor label is loyalty effect; army-turn ownership drift uses it as the per-turn loyalty gain");
        replaceAt(governmentDef, 0x38, IntegerDataType.dataType, 4, "city_limit",
            "editor label is city limit; City_Building_AI compares total force/unit count against this government threshold");
        replaceAt(governmentDef, 0x3c, IntegerDataType.dataType, 4, "recruitment_unrest",
            "editor label is unrest from recruiting soldiers");
        replaceAt(governmentDef, 0x40, new ArrayDataType(IntegerDataType.dataType, 11, 4), 0x2c,
            "research_efficiency_modifiers", "City_Resource_Change indexes this eleven-dword block by country research_efficiency_level");
        replaceAt(governmentDef, 0x6c, IntegerDataType.dataType, 4, "revolution_turns",
            "editor label is revolution turns");
        replaceAt(governmentDef, 0x70, IntegerDataType.dataType, 4, "allowed_unrest",
            "editor label is allowed unrest");
        resolve(governmentDef);

        groundDef = fixedStruct("GroundDef_0x24", 0x24);
        replaceAt(groundDef, 0x00, new ArrayDataType(CharDataType.dataType, 5, 1), 5,
            "surface_name_bytes", "editor label is terrain-surface name");
        replaceAt(groundDef, 0x08, IntegerDataType.dataType, 4, "irrigation_farmland_enabled",
            "editor label is irrigation farmland; Irrigate_Able requires this to be nonzero");
        replaceAt(groundDef, 0x0c, IntegerDataType.dataType, 4, "pasture_enabled",
            "editor label is pasture/ranch; Pasturage_Able requires this to be nonzero");
        replaceAt(groundDef, 0x10, IntegerDataType.dataType, 4, "fishery_enabled",
            "editor label is maritime fishery; Fish_Able requires this to be nonzero");
        replaceAt(groundDef, 0x14, IntegerDataType.dataType, 4, "food_output",
            "editor label is food output");
        replaceAt(groundDef, 0x18, IntegerDataType.dataType, 4, "gold_output",
            "editor label is gold output");
        replaceAt(groundDef, 0x1c, IntegerDataType.dataType, 4, "energy_output",
            "editor label is energy output");
        replaceAt(groundDef, 0x20, IntegerDataType.dataType, 4, "hillside_food_output",
            "editor label is hillside food");
        resolve(groundDef);

        empireCountryDef = fixedStruct("EmpireCountryDef_0x200", 0x200);
        replaceAt(empireCountryDef, 0x00, IntegerDataType.dataType, 4, "is_enabled_or_selectable",
            "custom-map selection and editor paths require this first dword to be positive");
        replaceAt(empireCountryDef, 0x04, new ArrayDataType(CharDataType.dataType, 17, 1), 17,
            "country_name_bytes", "editor label is country name");
        replaceAt(empireCountryDef, 0x15, new ArrayDataType(CharDataType.dataType, 17, 1), 17,
            "capital_name_bytes", "editor label is capital name");
        replaceAt(empireCountryDef, 0x26, new ArrayDataType(CharDataType.dataType, 17, 1), 17,
            "alliance_name_bytes", "editor label is alliance name");
        replaceAt(empireCountryDef, 0x38, IntegerDataType.dataType, 4, "country_profile_id",
            "editor label is leader/person; indexes g_country_profile_defs in custom-map selection, diplomacy, and editor-finish resource setup");
        replaceAt(empireCountryDef, 0x3c, IntegerDataType.dataType, 4, "flag_resource_id",
            "editor label is flag number");
        replaceAt(empireCountryDef, 0x40, IntegerDataType.dataType, 4, "origin_tile_x",
            "editor label is origin X; custom-map selection validates it against map width and passability");
        replaceAt(empireCountryDef, 0x44, IntegerDataType.dataType, 4, "origin_tile_y",
            "editor label is origin Y; custom-map selection validates it against map height and passability");
        replaceAt(empireCountryDef, 0x58, IntegerDataType.dataType, 4, "building_style_id",
            "editor label is building style; diplomacy UI loading branches on values 1 and 3");
        replaceAt(empireCountryDef, 0x5c, IntegerDataType.dataType, 4, "settlement_marker_id",
            "editor label is settlement marker");
        replaceAt(empireCountryDef, 0x60, IntegerDataType.dataType, 4, "favored_science_era_or_group",
            "City_Resource_Change compares this against ScienceDef.era_or_group_id for research pacing");
        replaceAt(empireCountryDef, 0x80, IntegerDataType.dataType, 4, "scenario_visibility_region_mode",
            "Add_New_View and Del_Army_View use this in gameplay mode 1 to limit visibility to a fixed map region");
        replaceAt(empireCountryDef, 0x88, IntegerDataType.dataType, 4, "diplomacy_affinity_threshold",
            "Diplomat_Turn compares diplomacy affinity/counters against this leader/country parameter");
        replaceAt(empireCountryDef, 0x8c, IntegerDataType.dataType, 4, "diplomacy_pressure_threshold",
            "Diplomat_Turn subtracts this from diplomatic pressure/caution thresholds");
        replaceAt(empireCountryDef, 0x90, IntegerDataType.dataType, 4, "ai_expedition_radius",
            "AI_Army uses this as the random expedition/search radius around its active city");
        replaceAt(empireCountryDef, 0x94, IntegerDataType.dataType, 4, "category4_build_bonus",
            "City_Building adds value-6 build progress for completed category 4 buildings when positive");
        replaceAt(empireCountryDef, 0x98, IntegerDataType.dataType, 4, "category5_build_bonus",
            "City_Building adds value-6 build progress for completed category 5 buildings when positive");
        replaceAt(empireCountryDef, 0x9c, IntegerDataType.dataType, 4, "unit_or_category2_build_bonus",
            "City_Building adds value-6 build progress for unit production and category 2 buildings when positive");
        replaceAt(empireCountryDef, 0xb4, IntegerDataType.dataType, 4, "category6_build_bonus",
            "City_Building adds value-6 build progress for category 6 buildings when paired gate is positive");
        replaceAt(empireCountryDef, 0xb8, IntegerDataType.dataType, 4, "category6_build_bonus_gate",
            "City_Building requires this value positive before applying the category 6 build bonus");
        replaceAt(empireCountryDef, 0xcc, IntegerDataType.dataType, 4, "diplomacy_battle_music_id",
            "Diplomat_Battle_Back passes this to the audio/theme switcher for the selected side");
        replaceAt(empireCountryDef, 0xd0, new ArrayDataType(IntegerDataType.dataType, 10, 4), 0x28,
            "special_army_type_ids", "editor label is special army type; paired with required science ids");
        replaceAt(empireCountryDef, 0xf8, new ArrayDataType(IntegerDataType.dataType, 10, 4), 0x28,
            "special_army_required_science_ids", "editor label is required science for each special army type");
        replaceAt(empireCountryDef, 0x120, IntegerDataType.dataType, 4, "diplomacy_ui_color_layer_a",
            "MLP_Edit_Empire_Country writes a palette row here; Edit_Finish and Load_Dat combine it with diplomacy UI color/image tables");
        replaceAt(empireCountryDef, 0x124, IntegerDataType.dataType, 4, "diplomacy_ui_color_layer_b",
            "MLP_Edit_Empire_Country writes a palette row here; Edit_Finish and Load_Dat combine it with diplomacy UI color/image tables");
        replaceAt(empireCountryDef, 0x128, IntegerDataType.dataType, 4, "diplomacy_ui_color_layer_c",
            "MLP_Edit_Empire_Country writes a palette row here; Edit_Finish and Load_Dat combine it with diplomacy UI color/image tables");
        resolve(empireCountryDef);

        resolve(new TypedefDataType(cat, "CityPtr", new PointerDataType(city, dtm)));
        resolve(new TypedefDataType(cat, "LandTilePtr", new PointerDataType(landTile, dtm)));
        resolve(new TypedefDataType(cat, "CountryStatePtr", new PointerDataType(country, dtm)));
        resolve(new TypedefDataType(cat, "ArmyUnitPtr", new PointerDataType(armyUnit, dtm)));
        resolve(new TypedefDataType(cat, "ArmyTypeDefPtr", new PointerDataType(armyTypeDef, dtm)));
    }

    private void renameFunctions() {
        Rename[] renames = new Rename[] {
            new Rename(0x401000L, "AI_ActShip"),
            new Rename(0x401d40L, "AI_AirOilPlane"),
            new Rename(0x4027f0L, "AI_AirPlane"),
            new Rename(0x403520L, "AI_Army"),
            new Rename(0x404780L, "AI_Carrier"),
            new Rename(0x405540L, "AI_Diplomat"),
            new Rename(0x406ff0L, "AI_Ship"),
            new Rename(0x408ec0L, "AI_Transport"),
            new Rename(0x4094b0L, "AI_UnClear"),
            new Rename(0x409960L, "AI_Worker"),
            new Rename(0x4086e0L, "NewLand_Name"),
            new Rename(0x40b450L, "Process_CommandLine_Args"),
            new Rename(0x40b580L, "Start_Map_Battle_From_Army"),
            new Rename(0x411ea0L, "City_Capture_Transfer"),
            new Rename(0x4131f0L, "Add_New_View"),
            new Rename(0x413b40L, "Del_Army_View"),
            new Rename(0x414b70L, "Battle_Peace_Place"),
            new Rename(0x414c50L, "Battle_First_Line"),
            new Rename(0x415600L, "Battle_AutoArrange"),
            new Rename(0x415cb0L, "Do_Battle_Army_And_Battle_Die"),
            new Rename(0x418510L, "Prepare_Battle_Tile_Object_Flags"),
            new Rename(0x418830L, "BattleArmy"),
            new Rename(0x4189c0L, "Decode_Battle"),
            new Rename(0x419240L, "Make_Battle_Map"),
            new Rename(0x419bd0L, "Do_Battle_Stone"),
            new Rename(0x419f30L, "Battle_Arrange_Position"),
            new Rename(0x41a9f0L, "City_Belong_Change"),
            new Rename(0x41b0f0L, "Army_Belong_Change"),
            new Rename(0x41b4a0L, "Bridge_Able"),
            new Rename(0x41b6c0L, "Irrigate_Able"),
            new Rename(0x41b830L, "Pasturage_Able"),
            new Rename(0x41b880L, "Mine_Able"),
            new Rename(0x41b8c0L, "Fish_Able"),
            new Rename(0x41b920L, "LongWall_Able"),
            new Rename(0x41b960L, "Resource_Able"),
            new Rename(0x41daf0L, "UserSet_City_Resource"),
            new Rename(0x41dea0L, "Cal_City_JobPeople"),
            new Rename(0x41e200L, "Cal_City_Resource"),
            new Rename(0x41f700L, "City_Happy_Change"),
            new Rename(0x41f730L, "City_Safe_Change"),
            new Rename(0x41f7c0L, "City_Loyal_Change"),
            new Rename(0x41f7f0L, "City_Business_Change"),
            new Rename(0x41f880L, "City_People_Change_Percent"),
            new Rename(0x41f8c0L, "City_Like_Change"),
            new Rename(0x41f9a0L, "App_Frame_Pump"),
            new Rename(0x41fab0L, "Game_Frame_Pump"),
            new Rename(0x4215f0L, "City_Building"),
            new Rename(0x420820L, "App_WinMain_Entry"),
            new Rename(0x422840L, "City_Building_AI"),
            new Rename(0x424d30L, "City_Build_AI_Build_Able"),
            new Rename(0x425070L, "City_Business"),
            new Rename(0x4254a0L, "City_Event_Happen"),
            new Rename(0x425940L, "City_Manager"),
            new Rename(0x425bd0L, "City_People_Born_Rate"),
            new Rename(0x425f10L, "City_People_Change"),
            new Rename(0x426380L, "City_Resource_Change"),
            new Rename(0x427bb0L, "City_Round_Check"),
            new Rename(0x428bf0L, "City_Size_Scale"),
            new Rename(0x428f20L, "City_Upgrade"),
            new Rename(0x429130L, "City_View"),
            new Rename(0x429930L, "Event_City_View"),
            new Rename(0x430370L, "Decode_City"),
            new Rename(0x431800L, "Decode_NewMap"),
            new Rename(0x433020L, "Decode_LongWall"),
            new Rename(0x433810L, "Decode_Road"),
            new Rename(0x433da0L, "Decode_MiniMap"),
            new Rename(0x438490L, "Diplomat_Go_Buy_City"),
            new Rename(0x4389c0L, "Diplomat_Ask_Surrend"),
            new Rename(0x438e20L, "Diplomat_Steal_Science"),
            new Rename(0x4393f0L, "Diplomat_ScareMonger"),
            new Rename(0x439880L, "Diplomat_Crack_Build"),
            new Rename(0x439d70L, "Diplomat_Commotion"),
            new Rename(0x43dec0L, "Diplomat_Start"),
            new Rename(0x43ebf0L, "Diplomat_Talking"),
            new Rename(0x43ece0L, "Diplomat_Answer_Cond_Check"),
            new Rename(0x43ee60L, "Diplomat_Allow"),
            new Rename(0x43f750L, "Diplomat_Value"),
            new Rename(0x440de0L, "Diplomat_AskWhat"),
            new Rename(0x441600L, "Diplomat_Ask_Check"),
            new Rename(0x442430L, "Diplomat_Compare"),
            new Rename(0x442aa0L, "Reflash_Dip_City_List"),
            new Rename(0x443c30L, "Diplomat_End"),
            new Rename(0x44ad80L, "Diplomat_Running"),
            new Rename(0x44b460L, "Diplomat_Turn"),
            new Rename(0x420a30L, "Font_Select"),
            new Rename(0x420ba0L, "Draw_Text_Centered"),
            new Rename(0x420c00L, "Draw_Text"),
            new Rename(0x42eed0L, "NodeInsert_DataFormat"),
            new Rename(0x42f210L, "NodeDelete_DataFormat"),
            new Rename(0x42f290L, "Add_New_DataFormat"),
            new Rename(0x42f3e0L, "Reflash_DataFormat"),
            new Rename(0x42f5c0L, "Del_DataFormat"),
            new Rename(0x42f600L, "CheckPress_DataFormat"),
            new Rename(0x42b7c0L, "CountryPoint_Minus"),
            new Rename(0x4578a0L, "Before_Edit_Empire_Country"),
            new Rename(0x452110L, "Before_Edit_Army"),
            new Rename(0x454570L, "Before_Edit_Build"),
            new Rename(0x45d6f0L, "Before_Edit_Goverment"),
            new Rename(0x45e4d0L, "Before_Edit_Ground"),
            new Rename(0x45ee10L, "Before_Edit_Empire_Hero"),
            new Rename(0x450490L, "Do_City"),
            new Rename(0x4514f0L, "Prepare_City_Doing"),
            new Rename(0x451bb0L, "Do_CityArmy"),
            new Rename(0x451de0L, "Do_Map"),
            new Rename(0x456c50L, "After_Edit_Country"),
            new Rename(0x464a20L, "Clear_UnUsed_Science"),
            new Rename(0x467010L, "Before_Edit_Science_Power"),
            new Rename(0x467250L, "Before_Edit_Science_Set"),
            new Rename(0x467740L, "Science_Know_With_Prerequisites"),
            new Rename(0x467dc0L, "Put_Edit_Science_Exp"),
            new Rename(0x4596a0L, "Before_Window_Edit_File_Detail"),
            new Rename(0x459f90L, "Put_Edit_File_Detail"),
            new Rename(0x458d80L, "MLP_Edit_Empire_Country"),
            new Rename(0x45b1d0L, "MouseOn_Edit_Sel_Custom_Map"),
            new Rename(0x45b2f0L, "MLR_Edit_SelCustomMap"),
            new Rename(0x45c330L, "MouseOn_Edit_Sel_Pcx_File"),
            new Rename(0x45c5d0L, "Before_Edit_Empire_Flag"),
            new Rename(0x45c640L, "After_Edit_Empire_Flag"),
            new Rename(0x45d0d0L, "Save_IMG_Flag"),
            new Rename(0x45d2c0L, "MLP_Edit_Empire_Flag"),
            new Rename(0x469c00L, "MakeFadeColorTable"),
            new Rename(0x46a1f0L, "Report_DirectDraw_Error"),
            new Rename(0x46a380L, "City_Army_Error_Fix"),
            new Rename(0x46a840L, "Add_New_Explode"),
            new Rename(0x46ab60L, "Find_Direct"),
            new Rename(0x46b850L, "Load_UI_String_EMG"),
            new Rename(0x46cc70L, "Load_UI_String_EMG_XMG"),
            new Rename(0x46d310L, "Init_DirectDraw_Runtime"),
            new Rename(0x46e950L, "Init_SetUp"),
            new Rename(0x473270L, "Load_Dat"),
            new Rename(0x478eb0L, "MainMenu_Init"),
            new Rename(0x4789e0L, "Load_EMG_Resource"),
            new Rename(0x478ac0L, "Load_XMG_Resource"),
            new Rename(0x478b30L, "Free_EMG_Resource"),
            new Rename(0x478b90L, "Free_XMG_Resource"),
            new Rename(0x478a50L, "Safe_LoadIMG"),
            new Rename(0x478b60L, "Safe_FreeIMG"),
            new Rename(0x477ff0L, "Load_EMG_Base"),
            new Rename(0x4788c0L, "Free_EMG_Base"),
            new Rename(0x478dc0L, "CloseIndexIMG"),
            new Rename(0x479000L, "MainMenu_Quit"),
            new Rename(0x479040L, "PutScreen_Mainmenu"),
            new Rename(0x479420L, "MLR_MainMenu"),
            new Rename(0x47b530L, "Reflash_City_Road"),
            new Rename(0x47b890L, "Make_City_Map"),
            new Rename(0x47be60L, "Make_City_Wall"),
            new Rename(0x47c040L, "Make_City_Culvert"),
            new Rename(0x47c2a0L, "Del_City_Wall_Or_Culvert"),
            new Rename(0x47c330L, "Make_City_Train"),
            new Rename(0x47c8b0L, "Map_To_Battle_Army"),
            new Rename(0x477800L, "Load_Map_GameInfo"),
            new Rename(0x47e230L, "Load_MAINMENU_EMG"),
            new Rename(0x47ee50L, "Menu_EditMenu_Init"),
            new Rename(0x47eef0L, "Menu_EditMenu_Quit"),
            new Rename(0x47f0a0L, "Put_Sub_EditMenu"),
            new Rename(0x47f910L, "MLR_NewEdit"),
            new Rename(0x4891a0L, "UI_YesNo_Dialog"),
            new Rename(0x489580L, "UI_YesNo_Message"),
            new Rename(0x4896d0L, "UI_YesNo_Result"),
            new Rename(0x48dc10L, "Near_Beach_City_Found"),
            new Rename(0x48ded0L, "Near_Beach_City_With_Army_Found"),
            new Rename(0x48e210L, "Near_Beach_City_Cap_Army_Found"),
            new Rename(0x48e6a0L, "Near_City_With_Army_Found"),
            new Rename(0x48e8d0L, "Near_City_Found_XY"),
            new Rename(0x48eae0L, "Near_City_Found_XY_NoLand"),
            new Rename(0x48ec50L, "Near_City_Found_CapAble"),
            new Rename(0x48edd0L, "InRange_NearDest_City_Found"),
            new Rename(0x48efa0L, "Near_City_With_Air_Found"),
            new Rename(0x48f1e0L, "Near_City_Away_Enemy"),
            new Rename(0x48f3b0L, "NoDpa_Near_City_Away_Enemy"),
            new Rename(0x48f620L, "NoDpa_Near_City_Near_Sea"),
            new Rename(0x48f980L, "Near_City_UserKnow_Found"),
            new Rename(0x48faa0L, "NoDpa_Near_City_Found"),
            new Rename(0x48c8f0L, "CheckMouseOnWindow"),
            new Rename(0x4711f0L, "JoinTo"),
            new Rename(0x471380L, "BreakOut"),
            new Rename(0x496df0L, "Start_Map_Battle_From_Tile"),
            new Rename(0x492760L, "Do_Country_Diplomat"),
            new Rename(0x4912e0L, "Do_Army_TurnJob"),
            new Rename(0x4939c0L, "Clear_Forest_Or_Resource"),
            new Rename(0x493a30L, "Make_New_Work"),
            new Rename(0x493be0L, "Make_New_Make"),
            new Rename(0x494110L, "Order_Check"),
            new Rename(0x4951e0L, "Order_Follower_UseAble"),
            new Rename(0x495320L, "Order_Diplomat_Choice_Mission"),
            new Rename(0x495540L, "Order_Spy_Choice_Mission"),
            new Rename(0x495780L, "Order_Diplomat_Sel_Buy"),
            new Rename(0x4959a0L, "Order_Diplomat_Sel_Take_City_or_Diplomat"),
            new Rename(0x495a50L, "Order_Diplomat_Sel_Take_City"),
            new Rename(0x495c90L, "Order_Forset"),
            new Rename(0x496180L, "Order_Go"),
            new Rename(0x496550L, "Order_Go_Act"),
            new Rename(0x4966e0L, "Order_Guard"),
            new Rename(0x496bd0L, "Order_Join_Sel"),
            new Rename(0x496d40L, "Order_Join_All"),
            new Rename(0x498950L, "Order_Nothing"),
            new Rename(0x498f00L, "Order_Out"),
            new Rename(0x499010L, "Order_Out_All"),
            new Rename(0x499090L, "Apply_OrderQueue_Army"),
            new Rename(0x49bec0L, "Load_TMG_Background"),
            new Rename(0x49e580L, "Put_City_View"),
            new Rename(0x49fd10L, "Edit_Start"),
            new Rename(0x49fe50L, "Edit_Finish"),
            new Rename(0x4b0c00L, "Read_Keyboard"),
            new Rename(0x4b0130L, "Add_OrderQueue_Army"),
            new Rename(0x4b3330L, "Read_MLP_Edit"),
            new Rename(0x4b6d70L, "MLR_Edit_GameMap"),
            new Rename(0x4b80c0L, "Read_MRP_Edit"),
            new Rename(0x4b8db0L, "Read_MRR_Edit"),
            new Rename(0x4b8820L, "Clear_Mountain"),
            new Rename(0x4b8f60L, "Cancel_All_Army_On_Tile"),
            new Rename(0x4bc720L, "PlayGame_Init"),
            new Rename(0x4c0350L, "Science_Know"),
            new Rename(0x4c05e0L, "Science_Next"),
            new Rename(0x4c2da0L, "Apply_Resolution_Mode"),
            new Rename(0x4c35f0L, "Set_Color"),
            new Rename(0x4c60a0L, "ShutDown_Game"),
            new Rename(0x4c6490L, "Clear_All_Memory"),
            new Rename(0x4c6e60L, "DiagCoords_To_TileX"),
            new Rename(0x4c6e80L, "DiagCoords_To_TileY"),
            new Rename(0x4c6e90L, "Tile_To_DiagCoordA"),
            new Rename(0x4c6eb0L, "Tile_To_DiagCoordB"),
            new Rename(0x4d2cc0L, "TestRoad"),
            new Rename(0x4c50d0L, "Draw_MainMenu_Number"),
            new Rename(0x4d91a0L, "Put_City_Citizen"),
            new Rename(0x4d40f0L, "Trace_Function"),
            new Rename(0x4df2e0L, "Put_City_Make"),
            new Rename(0x4ec1a0L, "Load_UI_DIP_EMG"),
            new Rename(0x4af830L, "Build_Dark_Table_From_Fade_Frame"),
            new Rename(0x4af8f0L, "Build_Dark_Table"),
            new Rename(0x4f0030L, "Lock_Back_Surface"),
            new Rename(0x4f0070L, "Unlock_Back_Surface"),
            new Rename(0x4f02d0L, "Present_Dirty_Rects"),
            new Rename(0x4f0afdL, "Set_Display_Mode_From_Mode_Table"),
            new Rename(0x4f0ce0L, "Create_Front_Surface"),
            new Rename(0x4f0de0L, "Create_Back_Surface"),
            new Rename(0x4f5ce9L, "Draw_Image_To_Backbuffer"),
            new Rename(0x4f4f60L, "Init_Pixel_Format_Tables"),
            new Rename(0x4f8660L, "Free_Pixel_Format_Tables"),
            new Rename(0x4681d0L, "Pixel16_To_Luminance_Level"),
            new Rename(0x4682a0L, "Decode_Pixel16_RGB"),
            new Rename(0x468320L, "MakeColorTable"),
            new Rename(0x4f81e0L, "Init_Surface_Pixel_State"),
            new Rename(0x4f00b0L, "Get_Game_Tick"),
            new Rename(0x4fa910L, "Clear_Surface"),
            new Rename(0x5035c0L, "Set_Draw_Clip_Rect"),
            new Rename(0x503730L, "Format_Text"),
            new Rename(0x41f900L, "Restore_DirectDraw_Surfaces"),
            new Rename(0x5047f0L, "Fatal_Exit")
        };
        for (Rename r : renames) {
            Function fn = getFunctionAt(addr(r.va));
            if (fn == null) {
                fn = getFunctionContaining(addr(r.va));
            }
            if (fn != null) {
                try {
                    fn.setName(r.name, SourceType.USER_DEFINED);
                }
                catch (Exception e) {
                    println("rename function failed 0x" + Long.toHexString(r.va) + ": " + e.getMessage());
                }
            }
        }
    }

    private void renameGlobals() throws Exception {
        GlobalRename[] globals = new GlobalRename[] {
            new GlobalRename(0x0074a040L, "g_land_tiles", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x00588b84L, "g_map_width_tiles", IntegerDataType.dataType),
            new GlobalRename(0x00588b88L, "g_map_height_tiles", IntegerDataType.dataType),
            new GlobalRename(0x00588b8cL, "g_map_width_tiles_cached", IntegerDataType.dataType),
            new GlobalRename(0x00588b90L, "g_map_half_height_tiles", IntegerDataType.dataType),
            new GlobalRename(0x007350b8L, "g_country_states", new ArrayDataType(country, 24, country.getLength())),
            new GlobalRename(0x00749a54L, "g_active_country_index", IntegerDataType.dataType),
            new GlobalRename(0x0074c82cL, "g_human_country_index", IntegerDataType.dataType),
            new GlobalRename(0x00706948L, "g_city_turn_list_head", new PointerDataType(city, dtm)),
            new GlobalRename(0x00749184L, "g_current_city", new PointerDataType(city, dtm)),
            new GlobalRename(0x00748e04L, "g_active_country", new PointerDataType(country, dtm)),
            new GlobalRename(0x00755980L, "g_current_city_land_tile", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x0074c81cL, "g_current_city_x", UnsignedIntegerDataType.dataType),
            new GlobalRename(0x0074c820L, "g_current_city_y", UnsignedIntegerDataType.dataType),
            new GlobalRename(0x00706880L, "g_city_turn_income_delta", IntegerDataType.dataType),
            new GlobalRename(0x00706884L, "g_city_turn_food_delta", IntegerDataType.dataType),
            new GlobalRename(0x00706888L, "g_city_turn_resource_delta", IntegerDataType.dataType),
            new GlobalRename(0x007068e8L, "g_city_should_auto_manage", ByteDataType.dataType),
            new GlobalRename(0x007068eaL, "g_city_removed_this_turn", ByteDataType.dataType),
            new GlobalRename(0x0070694cL, "g_city_turn_total_delta", IntegerDataType.dataType),
            new GlobalRename(0x0074c6c0L, "g_world_age_or_turn_phase", IntegerDataType.dataType),
            new GlobalRename(0x00755928L, "g_map_size_mode", IntegerDataType.dataType),
            new GlobalRename(0x00755964L, "g_auto_turn_or_ai_control_flag", IntegerDataType.dataType),
            new GlobalRename(0x005d9258L, "g_battle_grid_cells", new ArrayDataType(battleGridCell, 0x240, battleGridCell.getLength())),
            new GlobalRename(0x005d925cL, "g_battle_grid_base_tile_image_indices", IntegerDataType.dataType),
            new GlobalRename(0x005d9260L, "g_battle_grid_overlay_tile_image_indices", IntegerDataType.dataType),
            new GlobalRename(0x005d9264L, "g_battle_grid_terrain_variants", IntegerDataType.dataType),
            new GlobalRename(0x005d9268L, "g_battle_grid_region_markers", IntegerDataType.dataType),
            new GlobalRename(0x005d926cL, "g_battle_grid_front_units", new PointerDataType(battleUnit, dtm)),
            new GlobalRename(0x005d9270L, "g_battle_grid_front_aux_units", new PointerDataType(battleUnit, dtm)),
            new GlobalRename(0x005d9274L, "g_battle_grid_back_units", new PointerDataType(battleUnit, dtm)),
            new GlobalRename(0x005d9278L, "g_battle_grid_back_aux_units", new PointerDataType(battleUnit, dtm)),
            new GlobalRename(0x005d927cL, "g_battle_grid_effect_or_projectile", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005d9284L, "g_battle_grid_update_markers", IntegerDataType.dataType),
            new GlobalRename(0x005dfe68L, "g_battle_unit_count_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005dfe88L, "g_battle_unit_list_head_by_side", new ArrayDataType(new PointerDataType(battleUnit, dtm), 2, 4)),
            new GlobalRename(0x005d9234L, "g_battle_attacker_land_tile", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x005d9238L, "g_battle_defender_land_tile", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x005d9230L, "g_battle_tile_has_object_by_side", new ArrayDataType(ByteDataType.dataType, 2, 1)),
            new GlobalRename(0x005d9220L, "g_battle_attacker_slot_present", new ArrayDataType(IntegerDataType.dataType, 3, 4)),
            new GlobalRename(0x005dfe5cL, "g_battle_defender_slot_present", new ArrayDataType(IntegerDataType.dataType, 3, 4)),
            new GlobalRename(0x005d924cL, "g_battle_attacker_source_group_count", IntegerDataType.dataType),
            new GlobalRename(0x005d9250L, "g_battle_defender_source_group_count", IntegerDataType.dataType),
            new GlobalRename(0x005d9244L, "g_battle_total_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005d9210L, "g_battle_land_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005dfe7cL, "g_battle_air_or_class1_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005d9208L, "g_battle_special_or_class2_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005d9218L, "g_battle_frontline_land_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005d923cL, "g_battle_ranged_land_units_by_side", new ArrayDataType(IntegerDataType.dataType, 2, 4)),
            new GlobalRename(0x005aa2c8L, "g_army_type_table", new ArrayDataType(armyTypeDef, 0x5b, armyTypeDef.getLength())),
            new GlobalRename(0x005dfedcL, "g_directdraw_ready", IntegerDataType.dataType),
            new GlobalRename(0x005dfee0L, "g_main_window", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005dfed8L, "g_app_screen_state", IntegerDataType.dataType),
            new GlobalRename(0x005cfe64L, "g_pixel_red_bits", ByteDataType.dataType),
            new GlobalRename(0x005cfe65L, "g_pixel_green_bits", ByteDataType.dataType),
            new GlobalRename(0x005cfe66L, "g_pixel_blue_bits", ByteDataType.dataType),
            new GlobalRename(0x005cfe6cL, "g_pixel_red_shift", ByteDataType.dataType),
            new GlobalRename(0x005cfe6dL, "g_pixel_green_shift", ByteDataType.dataType),
            new GlobalRename(0x005cfe6eL, "g_pixel_blue_shift", ByteDataType.dataType),
            new GlobalRename(0x005cfe78L, "g_pixel_red_mask", UnsignedIntegerDataType.dataType),
            new GlobalRename(0x005cfe7cL, "g_pixel_green_mask", UnsignedIntegerDataType.dataType),
            new GlobalRename(0x005cfe80L, "g_pixel_blue_mask", UnsignedIntegerDataType.dataType),
            new GlobalRename(0x005cfe98L, "g_rgb_to_pixel_tables", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cfe9cL, "g_green_to_pixel_table", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cfea0L, "g_blue_to_pixel_table", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cfea4L, "g_alpha_blend_component_tables", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cfea8L, "g_alpha_blend_green_table", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cfeacL, "g_alpha_blend_blue_table", new PointerDataType(IntegerDataType.dataType, dtm)),
            new GlobalRename(0x005cff66L, "g_luminance_plus_table", new PointerDataType(UnsignedShortDataType.dataType, dtm)),
            new GlobalRename(0x005cff6aL, "g_luminance_minus_table", new PointerDataType(UnsignedShortDataType.dataType, dtm)),
            new GlobalRename(0x00707958L, "g_color_transform_tables", new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 27, 4)),
            new GlobalRename(0x00707930L, "g_fade_color_tables", new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 10, 4)),
            new GlobalRename(0x007161f0L, "g_dark_table_buffer", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x0074d4dcL, "g_bestpath_temp_buffer", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x0074c84cL, "g_resource_score_buffer", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x00748f38L, "g_land_record_buffers", new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 22, 4)),
            new GlobalRename(0x007584c0L, "g_minimap_buffer", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x0074c830L, "g_edit_dest_round_buffers", new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 2, 4)),
            new GlobalRename(0x0074c838L, "g_map_interaction_mode", IntegerDataType.dataType),
            new GlobalRename(0x005dff90L, "g_ddraw", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005dff94L, "g_primary_surface", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005dff98L, "g_back_surface", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005cff4aL, "g_back_surface_locked", IntegerDataType.dataType),
            new GlobalRename(0x00734c08L, "g_client_width", IntegerDataType.dataType),
            new GlobalRename(0x00734c14L, "g_client_height", IntegerDataType.dataType),
            new GlobalRename(0x00734c10L, "g_center_offset_x_from_800", IntegerDataType.dataType),
            new GlobalRename(0x00734c0cL, "g_center_offset_y_from_600", IntegerDataType.dataType),
            new GlobalRename(0x00714e30L, "g_dirty_rect_width", IntegerDataType.dataType),
            new GlobalRename(0x00714e14L, "g_dirty_rect_height", IntegerDataType.dataType),
            new GlobalRename(0x0058940cL, "g_resolution_mode_index", IntegerDataType.dataType),
            new GlobalRename(0x00589410L, "g_resolution_width_table", new ArrayDataType(IntegerDataType.dataType, 3, 4)),
            new GlobalRename(0x0058941cL, "g_resolution_height_table", new ArrayDataType(IntegerDataType.dataType, 3, 4)),
            new GlobalRename(0x005997b8L, "g_building_defs", new ArrayDataType(buildingDef, 0x41, buildingDef.getLength())),
            new GlobalRename(0x005a19d4L, "g_special_project_defs", new ArrayDataType(specialProjectDef, 0x19, specialProjectDef.getLength())),
            new GlobalRename(0x00581778L, "g_science_priority_target_ids", new ArrayDataType(IntegerDataType.dataType, 12, 4)),
            new GlobalRename(0x005817a8L, "g_science_defs", new ArrayDataType(scienceDef, 200, scienceDef.getLength())),
            new GlobalRename(0x00596218L, "g_country_profile_defs", new ArrayDataType(countryProfileDef, 100, countryProfileDef.getLength())),
            new GlobalRename(0x00599288L, "g_government_defs", new ArrayDataType(governmentDef, 8, governmentDef.getLength())),
            new GlobalRename(0x00589428L, "g_ground_defs", new ArrayDataType(groundDef, 15, groundDef.getLength())),
            new GlobalRename(0x00589a18L, "g_empire_country_defs", new ArrayDataType(empireCountryDef, 100, empireCountryDef.getLength())),
            new GlobalRename(0x0075cf00L, "g_present_use_blt_mode", IntegerDataType.dataType),
            new GlobalRename(0x0075cf18L, "g_present_dst_rect", new ArrayDataType(IntegerDataType.dataType, 4, 4)),
            new GlobalRename(0x0075cf38L, "g_present_src_left", IntegerDataType.dataType),
            new GlobalRename(0x0075cf3cL, "g_present_src_top", IntegerDataType.dataType),
            new GlobalRename(0x0075cf40L, "g_present_src_right", IntegerDataType.dataType),
            new GlobalRename(0x0075cf44L, "g_present_src_bottom", IntegerDataType.dataType),
            new GlobalRename(0x0075cf50L, "g_present_src_rect", new ArrayDataType(IntegerDataType.dataType, 4, 4)),
            new GlobalRename(0x0075cf68L, "g_present_clip_rect", new ArrayDataType(IntegerDataType.dataType, 4, 4)),
            new GlobalRename(0x0075cf78L, "g_present_dest_offset_y", IntegerDataType.dataType),
            new GlobalRename(0x0075cf7cL, "g_present_dest_offset_x", IntegerDataType.dataType),
            new GlobalRename(0x0075cf80L, "g_present_width", IntegerDataType.dataType),
            new GlobalRename(0x0075cf84L, "g_present_height", IntegerDataType.dataType),
            new GlobalRename(0x0075cf98L, "g_back_surface_video_memory_flag", IntegerDataType.dataType),
            new GlobalRename(0x0057d078L, "g_dirty_rect_prev_x", IntegerDataType.dataType),
            new GlobalRename(0x0057d07cL, "g_dirty_rect_prev_y", IntegerDataType.dataType),
            new GlobalRename(0x0057d080L, "g_dirty_rect_x", IntegerDataType.dataType),
            new GlobalRename(0x0057d084L, "g_dirty_rect_y", IntegerDataType.dataType),
            new GlobalRename(0x00755984L, "g_loaded_tmg_background", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x00706ce0L, "g_flag_img_edit_backups", new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 100, 4)),
            new GlobalRename(0x00706e70L, "g_edit_flag_index", IntegerDataType.dataType),
            new GlobalRename(0x00758570L, "g_flag_img_bank", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x00755954L, "g_editor_mode_enabled", IntegerDataType.dataType),
            new GlobalRename(0x00755978L, "g_current_land_tile", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x00755908L, "g_editor_cursor_tile_x", IntegerDataType.dataType),
            new GlobalRename(0x0075590cL, "g_editor_cursor_tile_y", IntegerDataType.dataType),
            new GlobalRename(0x00716120L, "g_editor_land_tile_backup", new PointerDataType(landTile, dtm)),
            new GlobalRename(0x00708070L, "g_edit_menu_page", IntegerDataType.dataType),
            new GlobalRename(0x0070806cL, "g_edit_menu_hover_index", IntegerDataType.dataType),
            new GlobalRename(0x00708074L, "g_edit_menu_selected_mode", IntegerDataType.dataType),
            new GlobalRename(0x00708078L, "g_edit_menu_selected_map_size", IntegerDataType.dataType),
            new GlobalRename(0x0070807cL, "g_edit_menu_selected_template", IntegerDataType.dataType),
            new GlobalRename(0x007156d0L, "g_custom_map_hover_index", IntegerDataType.dataType),
            new GlobalRename(0x00571aacL, "g_selected_custom_map_index", IntegerDataType.dataType),
            new GlobalRename(0x0057ea5cL, "g_custom_map_action", IntegerDataType.dataType),
            new GlobalRename(0x0074c690L, "g_current_map_scenario_info", mapScenarioInfo),
            new GlobalRename(0x00706b30L, "g_custom_map_table", new PointerDataType(mapScenarioInfo, dtm)),
            new GlobalRename(0x00706cc4L, "g_custom_map_count", IntegerDataType.dataType),
            new GlobalRename(0x0057e94cL, "g_editor_tool_mode", IntegerDataType.dataType),
            new GlobalRename(0x00715da8L, "g_editor_brush_size_index", IntegerDataType.dataType),
            new GlobalRename(0x0074a360L, "g_tile_radius_offset_counts", new ArrayDataType(IntegerDataType.dataType, 5, 4)),
            new GlobalRename(0x0057eac0L, "g_editor_template_diag_offset_a", new ArrayDataType(IntegerDataType.dataType, 27, 4)),
            new GlobalRename(0x0057eb2cL, "g_editor_template_diag_offset_b", new ArrayDataType(IntegerDataType.dataType, 27, 4)),
            new GlobalRename(0x0057eb98L, "g_editor_template_terrain_kind", new ArrayDataType(ByteDataType.dataType, 27, 4)),
            new GlobalRename(0x0057ec04L, "g_editor_template_road_mode", new ArrayDataType(ByteDataType.dataType, 27, 4)),
            new GlobalRename(0x00588b80L, "g_request_redraw", ByteDataType.dataType),
            new GlobalRename(0x00716104L, "g_editor_left_press_active", IntegerDataType.dataType),
            new GlobalRename(0x00716108L, "g_editor_form_input_blocked", ByteDataType.dataType),
            new GlobalRename(0x00716109L, "g_editor_terrain_clear_guard", ByteDataType.dataType),
            new GlobalRename(0x00716124L, "g_editor_map_backup_state", IntegerDataType.dataType),
            new GlobalRename(0x00715da4L, "g_editor_ground_edit_submode", IntegerDataType.dataType),
            new GlobalRename(0x00715f70L, "g_editor_selected_terrain_kind", IntegerDataType.dataType),
            new GlobalRename(0x00716110L, "g_editor_selected_road_mode", IntegerDataType.dataType),
            new GlobalRename(0x0057e950L, "g_editor_overlay_action", IntegerDataType.dataType),
            new GlobalRename(0x0057e954L, "g_editor_overlay_kind", IntegerDataType.dataType),
            new GlobalRename(0x00716118L, "g_editor_selected_city_resource_id", IntegerDataType.dataType),
            new GlobalRename(0x00572a90L, "g_editor_resource_initial_stockpile", IntegerDataType.dataType),
            new GlobalRename(0x0057e994L, "g_editor_selected_country_id", IntegerDataType.dataType),
            new GlobalRename(0x0057e990L, "g_editor_selected_city_seed_id", IntegerDataType.dataType),
            new GlobalRename(0x0057e998L, "g_editor_selected_army_group", IntegerDataType.dataType),
            new GlobalRename(0x0057e99cL, "g_editor_selected_army_slot", IntegerDataType.dataType),
            new GlobalRename(0x007558fcL, "g_frame_tick", IntegerDataType.dataType),
            new GlobalRename(0x0074c0a0L, "g_menu_action_tick", IntegerDataType.dataType),
            new GlobalRename(0x00707f8cL, "g_menu_item_emg_resource", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x0070805cL, "g_mainmenu_emg_resource", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x00707f90L, "g_mainmenu_sprite_bank", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x00707f70L, "g_mainmenu_intro_completed_count", IntegerDataType.dataType),
            new GlobalRename(0x00707f74L, "g_mainmenu_intro_spawn_index", IntegerDataType.dataType),
            new GlobalRename(0x00707f7cL, "g_mainmenu_selected_index", IntegerDataType.dataType),
            new GlobalRename(0x00707f80L, "g_mainmenu_highlight_frame", IntegerDataType.dataType),
            new GlobalRename(0x00707f98L, "g_mainmenu_anim_state", IntegerDataType.dataType),
            new GlobalRename(0x00771f34L, "g_draw_sprite_fn", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x0077b1b4L, "g_view_center_x", IntegerDataType.dataType),
            new GlobalRename(0x0077b1c8L, "g_view_center_y", IntegerDataType.dataType),
            new GlobalRename(0x00758544L, "g_data_format_list_head", new PointerDataType(dataFormat, dtm)),
            new GlobalRename(0x00758548L, "g_data_format_list_tail", new PointerDataType(dataFormat, dtm))
        };
        for (GlobalRename g : globals) {
            Address a = addr(g.va);
            try {
                createLabel(a, g.name, true, SourceType.USER_DEFINED);
            }
            catch (Exception e) {
                println("label failed " + g.name + ": " + e.getMessage());
            }
            try {
                clearListing(a, a.add(Math.max(0, g.type.getLength() - 1)));
                createData(a, g.type);
            }
            catch (Exception e) {
                println("data type failed " + g.name + ": " + e.getMessage());
            }
        }
    }

    private void applySelectedSignatures() throws Exception {
        pointerArg(0x415cb0L, "Do_Battle_Army_And_Battle_Die", VoidDataType.dataType,
            "battle_unit", battleUnit);
        pointerArg(0x418830L, "BattleArmy", VoidDataType.dataType,
            "side", UnsignedIntegerDataType.dataType, "army", armyUnit, "formation_count", IntegerDataType.dataType,
            "stat_a", new PointerDataType(UnsignedIntegerDataType.dataType, dtm),
            "stat_b", new PointerDataType(UnsignedIntegerDataType.dataType, dtm));
        pointerArg(0x411ea0L, "City_Capture_Transfer", IntegerDataType.dataType,
            "city", city, "old_owner_country_id", IntegerDataType.dataType,
            "new_owner_country_id", IntegerDataType.dataType, "capture_mode", IntegerDataType.dataType);
        pointerArg(0x4131f0L, "Add_New_View", VoidDataType.dataType,
            "tile_x", IntegerDataType.dataType, "tile_y", UnsignedIntegerDataType.dataType,
            "view_radius_mode", IntegerDataType.dataType, "country_id", IntegerDataType.dataType,
            "force_visible", IntegerDataType.dataType, "zone_mask", IntegerDataType.dataType,
            "unit_class", IntegerDataType.dataType, "special_visibility", IntegerDataType.dataType);
        pointerArg(0x413b40L, "Del_Army_View", VoidDataType.dataType,
            "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType,
            "view_radius_mode", UnsignedIntegerDataType.dataType, "country_id", IntegerDataType.dataType,
            "special_visibility", IntegerDataType.dataType);
        pointerArg(0x41a9f0L, "City_Belong_Change", VoidDataType.dataType,
            "city", city, "new_owner_country_id", IntegerDataType.dataType);
        pointerArg(0x41b0f0L, "Army_Belong_Change", VoidDataType.dataType,
            "army", armyUnit, "new_owner_country_id", IntegerDataType.dataType);
        pointerArg(0x41b4a0L, "Bridge_Able", IntegerDataType.dataType, "tile", landTile);
        pointerArg(0x41b6c0L, "Irrigate_Able", ByteDataType.dataType, "tile", landTile,
            "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType,
            "allow_dry_neighbor", IntegerDataType.dataType);
        pointerArg(0x41b830L, "Pasturage_Able", ByteDataType.dataType, "tile", landTile);
        pointerArg(0x41b880L, "Mine_Able", ByteDataType.dataType, "tile", landTile);
        pointerArg(0x41b8c0L, "Fish_Able", ByteDataType.dataType, "tile", landTile);
        pointerArg(0x41b920L, "LongWall_Able", ByteDataType.dataType, "tile", landTile);
        pointerArg(0x41b960L, "Resource_Able", ByteDataType.dataType,
            "tile", landTile, "resource_id", IntegerDataType.dataType);
        pointerArg(0x41f700L, "City_Happy_Change", VoidDataType.dataType, "city", city, "delta", IntegerDataType.dataType);
        pointerArg(0x41f730L, "City_Safe_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f7c0L, "City_Loyal_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f7f0L, "City_Business_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f8c0L, "City_Like_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x4254a0L, "City_Event_Happen", VoidDataType.dataType, "city", city);
        pointerArg(0x42b7c0L, "CountryPoint_Minus", VoidDataType.dataType,
            "country_state", new PointerDataType(CharDataType.dataType, dtm));
        pointerArg(0x42eed0L, "NodeInsert_DataFormat", VoidDataType.dataType, "data_format", dataFormat);
        pointerArg(0x47c8b0L, "Map_To_Battle_Army", IntegerDataType.dataType, "army", armyUnit);
        pointerArg(0x46a840L, "Add_New_Explode", VoidDataType.dataType,
            "country_id", IntegerDataType.dataType, "tile_x", ShortDataType.dataType,
            "tile_y", ShortDataType.dataType);
        pointerArg(0x46ab60L, "Find_Direct", IntegerDataType.dataType,
            "from_tile_x", IntegerDataType.dataType, "from_tile_y", UnsignedIntegerDataType.dataType,
            "to_tile_x", IntegerDataType.dataType, "to_tile_y", IntegerDataType.dataType);
        pointerArg(0x4711f0L, "JoinTo", ByteDataType.dataType,
            "army", armyUnit, "target_army", armyUnit);
        pointerArg(0x471380L, "BreakOut", VoidDataType.dataType, "army", armyUnit);
        pointerArg(0x4939c0L, "Clear_Forest_Or_Resource", VoidDataType.dataType, "tile", landTile);
        pointerArg(0x493a30L, "Make_New_Work", VoidDataType.dataType,
            "tile", landTile, "work_kind", IntegerDataType.dataType);
        pointerArg(0x493be0L, "Make_New_Make", VoidDataType.dataType,
            "tile", landTile, "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType,
            "make_kind", IntegerDataType.dataType, "variant", ByteDataType.dataType);
        pointerArg(0x499090L, "Apply_OrderQueue_Army", VoidDataType.dataType,
            "army", armyUnit, "action_id", UnsignedIntegerDataType.dataType,
            "event_id", IntegerDataType.dataType, "result_action_id", IntegerDataType.dataType,
            "direction_or_mode", IntegerDataType.dataType, "related_army", armyUnit,
            "target_x", IntegerDataType.dataType, "target_y", IntegerDataType.dataType);
        pointerArg(0x4b0130L, "Add_OrderQueue_Army", VoidDataType.dataType,
            "army", armyUnit, "action_id", IntegerDataType.dataType,
            "event_id", IntegerDataType.dataType, "result_action_id", IntegerDataType.dataType,
            "direction_or_mode", IntegerDataType.dataType, "related_army", armyUnit,
            "target_x", IntegerDataType.dataType, "target_y", IntegerDataType.dataType);
        pointerArg(0x4c6e60L, "DiagCoords_To_TileX", IntegerDataType.dataType,
            "diag_a", IntegerDataType.dataType, "diag_b", IntegerDataType.dataType);
        pointerArg(0x4c6e80L, "DiagCoords_To_TileY", IntegerDataType.dataType,
            "diag_a", IntegerDataType.dataType, "diag_b", IntegerDataType.dataType);
        pointerArg(0x4c6e90L, "Tile_To_DiagCoordA", IntegerDataType.dataType,
            "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType);
        pointerArg(0x4c6eb0L, "Tile_To_DiagCoordB", IntegerDataType.dataType,
            "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType);
        pointerArg(0x4b8820L, "Clear_Mountain", VoidDataType.dataType,
            "tile_x", IntegerDataType.dataType, "tile_y", IntegerDataType.dataType);
        pointerArg(0x4b8f60L, "Cancel_All_Army_On_Tile", VoidDataType.dataType, "tile", landTile);
        pointerArg(0x4d2cc0L, "TestRoad", IntegerDataType.dataType, "army", armyUnit);
        pointerArg(0x4f02d0L, "Present_Dirty_Rects", VoidDataType.dataType,
            "dst_x", IntegerDataType.dataType, "dst_y", IntegerDataType.dataType);
    }

    private void pointerArg(long va, String name, DataType returnType, Object... args) throws Exception {
        Function fn = getFunctionAt(addr(va));
        if (fn == null) {
            return;
        }
        FunctionDefinitionDataType sig = new FunctionDefinitionDataType(cat, name);
        sig.setReturnType(returnType);
        ParameterDefinition[] params = new ParameterDefinition[args.length / 2];
        for (int i = 0; i < args.length; i += 2) {
            String argName = (String) args[i];
            Object typeObj = args[i + 1];
            DataType type = typeObj instanceof StructureDataType
                ? new PointerDataType((StructureDataType) typeObj, dtm)
                : (DataType) typeObj;
            params[i / 2] = new ParameterDefinitionImpl(argName, type, null);
        }
        sig.setArguments(params);
        ApplyFunctionSignatureCmd cmd = new ApplyFunctionSignatureCmd(
            fn.getEntryPoint(), sig, SourceType.USER_DEFINED, true, true);
        cmd.applyTo(currentProgram, monitor);
    }
}

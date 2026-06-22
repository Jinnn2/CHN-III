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
    private StructureDataType battleUnit;
    private StructureDataType tmgImage;

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
        landTile = fixedStruct("LandTile_0x100", 0x100);
        replaceAt(landTile, 0x10, ShortDataType.dataType, 2, "linked_count_or_city_count",
            "load_dat checks this count before rebuilding map links");
        replaceAt(landTile, 0x28, new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 10, 4), 0x28,
            "army_or_city_ptrs_a", "pointer list rebuilt in load_dat");
        replaceAt(landTile, 0x50, ByteDataType.dataType, 1, "army_count_or_occupant_count",
            "checked before iterating tile occupants");
        replaceAt(landTile, 0x54, new ArrayDataType(new PointerDataType(VoidDataType.dataType, dtm), 10, 4), 0x28,
            "army_or_city_ptrs_b", "secondary occupant pointer list");
        replaceAt(landTile, 0x7c, ByteDataType.dataType, 1, "secondary_occupant_count",
            "count-like field paired with army_count_or_occupant_count in city build/population checks");
        replaceAt(landTile, 0x88, new PointerDataType(VoidDataType.dataType, dtm), 4, "linked_record",
            "dereferenced during load-time repair");
        resolve(landTile);

        city = fixedStruct("City_0x1b8_plus", 0x1b8);
        replaceAt(city, 0x03, new ArrayDataType(ByteDataType.dataType, 32, 1), 32, "name_bytes",
            "name-like string is passed from city + 3");
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
        replaceAt(city, 0x177, ByteDataType.dataType, 1, "forced_event_pending", "one-turn city event flag");
        replaceAt(city, 0x181, ByteDataType.dataType, 1, "uses_manual_resource_setup", "selects resource setup path");
        replaceAt(city, 0x182, ByteDataType.dataType, 1, "processed_this_turn", "prevents duplicate do_city processing");
        replaceAt(city, 0x1b4, new PointerDataType(city, dtm), 4, "next_city", "city linked-list pointer");
        resolve(city);

        country = fixedStruct("CountryState_0xe68", 0xe68);
        replaceAt(country, 0x00, ByteDataType.dataType, 1, "is_active", "checked before per-country loops");
        replaceAt(country, 0x01, ByteDataType.dataType, 1, "leader_or_country_id", "compared against literal 0x22");
        replaceAt(country, 0x04, new ArrayDataType(ByteDataType.dataType, 32, 1), 32, "name_bytes", "used in diplomacy text");
        replaceAt(country, 0x38, new PointerDataType(city, dtm), 4, "capital_city",
            "city building completion stores the current city here when founding/capital-class buildings finish");
        replaceAt(country, 0x60, IntegerDataType.dataType, 4, "government_or_ai_mode", "city event condition");
        replaceAt(country, 0x7c, UnsignedShortDataType.dataType, 2, "owned_city_count",
            "used as divisor for per-city country pressure and diplomacy city-count checks");
        replaceAt(country, 0x688, DoubleDataType.dataType, 8, "science_budget_or_treasury", "used by city upgrade cost");
        replaceAt(country, 0x698, DoubleDataType.dataType, 8, "population_or_score_total", "increased when city removed");
        replaceAt(country, 0x63c, ByteDataType.dataType, 1, "special_rule_level", "city event condition");
        replaceAt(country, 0x6a0, ByteDataType.dataType, 1, "resource_pressure_level",
            "compared against government tables before city resource scoring");
        replaceAt(country, 0x6a1, ByteDataType.dataType, 1, "construction_efficiency_level",
            "scales construction/research production in City_Resource_Change");
        replaceAt(country, 0x6a2, ByteDataType.dataType, 1, "research_efficiency_level",
            "indexes government tables and scales research production");
        replaceAt(country, 0x6a3, ByteDataType.dataType, 1, "tax_efficiency_level",
            "combined with resource pressure for positive treasury delta display");
        replaceAt(country, 0x6a4, new ArrayDataType(IntegerDataType.dataType, 0x1c, 4), 0x70,
            "early_science_status", "early per-science status words; value 2 means completed/unlocked");
        replaceAt(country, 0x714, IntegerDataType.dataType, 4, "country_state_mode", "city event condition");
        replaceAt(country, 0x9c4, ShortDataType.dataType, 2, "build_or_draft_capacity", "worker allocation condition");
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
        resolve(country);

        battleUnit = fixedStruct("BattleUnit_approx", 0x40);
        replaceAt(battleUnit, 0x10, IntegerDataType.dataType, 4, "battle_x", "param_1[4] in battle grid logic");
        replaceAt(battleUnit, 0x14, IntegerDataType.dataType, 4, "battle_y", "param_1[5] in battle grid logic");
        replaceAt(battleUnit, 0x18, IntegerDataType.dataType, 4, "army_type", "param_1[6] indexes battle offsets");
        resolve(battleUnit);

        tmgImage = fixedStruct("DecodedImageHeader", 4);
        replaceAt(tmgImage, 0x00, UnsignedShortDataType.dataType, 2, "width", "draw routine reads first word");
        replaceAt(tmgImage, 0x02, UnsignedShortDataType.dataType, 2, "height", "draw routine reads second word");
        resolve(tmgImage);

        resolve(new TypedefDataType(cat, "CityPtr", new PointerDataType(city, dtm)));
        resolve(new TypedefDataType(cat, "LandTilePtr", new PointerDataType(landTile, dtm)));
        resolve(new TypedefDataType(cat, "CountryStatePtr", new PointerDataType(country, dtm)));
    }

    private void renameFunctions() {
        Rename[] renames = new Rename[] {
            new Rename(0x405540L, "AI_Diplomat"),
            new Rename(0x414b70L, "Battle_Peace_Place"),
            new Rename(0x414c50L, "Battle_First_Line"),
            new Rename(0x415600L, "Battle_AutoArrange"),
            new Rename(0x415cb0L, "Do_Battle_Army_And_Battle_Die"),
            new Rename(0x418830L, "BattleArmy"),
            new Rename(0x4189c0L, "Decode_Battle"),
            new Rename(0x419240L, "Make_Battle_Map"),
            new Rename(0x419bd0L, "Do_Battle_Stone"),
            new Rename(0x419f30L, "Battle_Arrange_Position"),
            new Rename(0x41a9f0L, "City_Belong_Change"),
            new Rename(0x41daf0L, "UserSet_City_Resource"),
            new Rename(0x41dea0L, "Cal_City_JobPeople"),
            new Rename(0x41e200L, "Cal_City_Resource"),
            new Rename(0x41f700L, "City_Happy_Change"),
            new Rename(0x41f730L, "City_Safe_Change"),
            new Rename(0x41f7c0L, "City_Loyal_Change"),
            new Rename(0x41f7f0L, "City_Business_Change"),
            new Rename(0x41f880L, "City_People_Change_Percent"),
            new Rename(0x41f8c0L, "City_Like_Change"),
            new Rename(0x4215f0L, "City_Building"),
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
            new Rename(0x450490L, "Do_City"),
            new Rename(0x4514f0L, "Prepare_City_Doing"),
            new Rename(0x451bb0L, "Do_CityArmy"),
            new Rename(0x451de0L, "Do_Map"),
            new Rename(0x46a1f0L, "Report_DirectDraw_Error"),
            new Rename(0x46a380L, "City_Army_Error_Fix"),
            new Rename(0x46b850L, "Load_UI_String_EMG"),
            new Rename(0x46cc70L, "Load_UI_String_EMG_XMG"),
            new Rename(0x46d310L, "Init_DirectDraw_Runtime"),
            new Rename(0x473270L, "Load_Dat"),
            new Rename(0x478eb0L, "MainMenu_Init"),
            new Rename(0x4789e0L, "Load_EMG_Resource"),
            new Rename(0x478ac0L, "Load_XMG_Resource"),
            new Rename(0x478b30L, "Free_EMG_Resource"),
            new Rename(0x478b90L, "Free_XMG_Resource"),
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
            new Rename(0x47e230L, "Load_MAINMENU_EMG"),
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
            new Rename(0x492760L, "Do_Country_Diplomat"),
            new Rename(0x495320L, "Order_Diplomat_Choice_Mission"),
            new Rename(0x495780L, "Order_Diplomat_Sel_Buy"),
            new Rename(0x4959a0L, "Order_Diplomat_Sel_Take_City_or_Diplomat"),
            new Rename(0x495a50L, "Order_Diplomat_Sel_Take_City"),
            new Rename(0x49bec0L, "Load_TMG_Background"),
            new Rename(0x49e580L, "Put_City_View"),
            new Rename(0x4c2da0L, "Apply_Resolution_Mode"),
            new Rename(0x4c50d0L, "Draw_MainMenu_Number"),
            new Rename(0x4d91a0L, "Put_City_Citizen"),
            new Rename(0x4d40f0L, "Trace_Function"),
            new Rename(0x4df2e0L, "Put_City_Make"),
            new Rename(0x4ec1a0L, "Load_UI_DIP_EMG"),
            new Rename(0x4f0030L, "Lock_Back_Surface"),
            new Rename(0x4f0070L, "Unlock_Back_Surface"),
            new Rename(0x4f02d0L, "Present_Dirty_Rects"),
            new Rename(0x4f0afdL, "Set_Display_Mode_From_Mode_Table"),
            new Rename(0x4f0ce0L, "Create_Front_Surface"),
            new Rename(0x4f0de0L, "Create_Back_Surface"),
            new Rename(0x4f5ce9L, "Draw_Image_To_Backbuffer"),
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
            new GlobalRename(0x005d926cL, "g_battle_grid_front_units", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005d9274L, "g_battle_grid_back_units", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005aa2c8L, "g_army_type_table", new ArrayDataType(ByteDataType.dataType, 0x100, 1)),
            new GlobalRename(0x005dfedcL, "g_directdraw_ready", IntegerDataType.dataType),
            new GlobalRename(0x005dfee0L, "g_main_window", new PointerDataType(VoidDataType.dataType, dtm)),
            new GlobalRename(0x005dfed8L, "g_app_screen_state", IntegerDataType.dataType),
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
            new GlobalRename(0x0077b1c8L, "g_view_center_y", IntegerDataType.dataType)
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
        pointerArg(0x41f700L, "City_Happy_Change", VoidDataType.dataType, "city", city, "delta", IntegerDataType.dataType);
        pointerArg(0x41f730L, "City_Safe_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f7c0L, "City_Loyal_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f7f0L, "City_Business_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x41f8c0L, "City_Like_Change", VoidDataType.dataType, "city", city);
        pointerArg(0x4254a0L, "City_Event_Happen", VoidDataType.dataType, "city", city);
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

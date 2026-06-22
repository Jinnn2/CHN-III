// Ghidra headless script.
// Run with:
// analyzeHeadless <project_dir> CHNIII -process China2EX_fontfix8.exe -noanalysis \
//   -scriptPath tools/reverse_probe -postScript GhidraExport.java <out_dir>

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

public class GhidraExport extends GhidraScript {
    private static class Target {
        long va;
        String path;
        Target(long va, String path) {
            this.va = va;
            this.path = path;
        }
    }

    private static final Target[] TARGETS = new Target[] {
        new Target(0x46d310L, "render/init_directdraw_runtime.c"),
        new Target(0x4789e0L, "ui/load_emg_resource.c"),
        new Target(0x478ac0L, "ui/load_xmg_resource.c"),
        new Target(0x478b30L, "ui/free_emg_resource.c"),
        new Target(0x478b90L, "ui/free_xmg_resource.c"),
        new Target(0x4788c0L, "ui/free_emg_base.c"),
        new Target(0x478b60L, "ui/safe_free_img.c"),
        new Target(0x478dc0L, "ui/close_index_img.c"),
        new Target(0x477ff0L, "render/load_emg_base.c"),
        new Target(0x478eb0L, "ui/main_menu_init.c"),
        new Target(0x479000L, "ui/main_menu_quit.c"),
        new Target(0x479040L, "ui/main_menu_putscreen.c"),
        new Target(0x479420L, "ui/main_menu_mouse_left_release.c"),
        new Target(0x49bec0L, "render/load_tmg_background.c"),
        new Target(0x4c2da0L, "render/apply_resolution_mode.c"),
        new Target(0x4f0030L, "render/lock_back_surface.c"),
        new Target(0x4f0070L, "render/unlock_back_surface.c"),
        new Target(0x4f02d0L, "render/present_dirty_rects.c"),
        new Target(0x4f0afdL, "render/set_display_mode_from_mode_table.c"),
        new Target(0x4f0ce0L, "render/create_front_surface.c"),
        new Target(0x4f0de0L, "render/create_back_surface.c"),
        new Target(0x4f4f60L, "render/init_pixel_format_tables.c"),
        new Target(0x4f81e0L, "render/init_surface_pixel_state.c"),
        new Target(0x4681d0L, "render/pixel16_to_luminance_level.c"),
        new Target(0x4682a0L, "render/decode_pixel16_rgb.c"),
        new Target(0x468320L, "render/make_color_table.c"),
        new Target(0x469c00L, "render/make_fade_color_table.c"),
        new Target(0x4af830L, "render/build_dark_table_from_fade_frame.c"),
        new Target(0x4af8f0L, "render/build_dark_table.c"),
        new Target(0x4f00b0L, "render/get_game_tick.c"),
        new Target(0x4fa910L, "render/clear_surface.c"),
        new Target(0x5035c0L, "render/set_draw_clip_rect.c"),
        new Target(0x503730L, "extra/format_text.c"),

        new Target(0x40b450L, "game/process_command_line_args.c"),
        new Target(0x41f9a0L, "game/app_frame_pump.c"),
        new Target(0x41fab0L, "game/game_frame_pump.c"),
        new Target(0x420820L, "game/app_winmain_entry.c"),
        new Target(0x46e950L, "game/init_setup.c"),
        new Target(0x4c35f0L, "game/set_color.c"),
        new Target(0x4c60a0L, "game/shutdown_game.c"),
        new Target(0x4c6490L, "game/clear_all_memory.c"),
        new Target(0x4f8660L, "render/free_pixel_format_tables.c"),

        new Target(0x40b580L, "game/start_map_battle_from_army.c"),
        new Target(0x414b70L, "game/battle_peace_place.c"),
        new Target(0x414c50L, "game/battle_first_line.c"),
        new Target(0x415600L, "game/battle_auto_arrange.c"),
        new Target(0x415cb0L, "game/do_battle_army_and_die.c"),
        new Target(0x418510L, "game/prepare_battle_tile_object_flags.c"),
        new Target(0x418830L, "game/battle_army.c"),
        new Target(0x4189c0L, "game/decode_battle.c"),
        new Target(0x419240L, "game/make_battle_map.c"),
        new Target(0x419bd0L, "game/do_battle_stone.c"),
        new Target(0x419f30L, "game/battle_arrange_position_and_ui_load.c"),

        new Target(0x41a9f0L, "game/city_belong_change.c"),
        new Target(0x41b4a0L, "game/bridge_able.c"),
        new Target(0x41b6c0L, "game/irrigate_able.c"),
        new Target(0x41b830L, "game/pasturage_able.c"),
        new Target(0x41b880L, "game/mine_able.c"),
        new Target(0x41b8c0L, "game/fish_able.c"),
        new Target(0x41b960L, "game/resource_able.c"),
        new Target(0x41daf0L, "game/user_set_city_resource.c"),
        new Target(0x41dea0L, "game/calc_city_job_people.c"),
        new Target(0x41e200L, "game/calc_city_resource.c"),
        new Target(0x41f700L, "game/city_happy_change.c"),
        new Target(0x41f730L, "game/city_safe_change.c"),
        new Target(0x41f7c0L, "game/city_loyal_change.c"),
        new Target(0x41f7f0L, "game/city_business_change.c"),
        new Target(0x41f880L, "game/city_people_change_percent.c"),
        new Target(0x41f8c0L, "game/city_like_change.c"),
        new Target(0x4215f0L, "game/city_building.c"),
        new Target(0x422840L, "game/city_building_ai.c"),
        new Target(0x424d30L, "game/city_build_ai_build_able.c"),
        new Target(0x425070L, "game/city_business.c"),
        new Target(0x4254a0L, "game/city_event_happen.c"),
        new Target(0x425940L, "game/city_manager.c"),
        new Target(0x425bd0L, "game/city_people_born_rate.c"),
        new Target(0x425f10L, "game/city_people_change.c"),
        new Target(0x426380L, "game/city_resource_change.c"),
        new Target(0x427bb0L, "game/city_round_check.c"),
        new Target(0x428bf0L, "game/city_size_scale.c"),
        new Target(0x428f20L, "game/city_upgrade.c"),
        new Target(0x429130L, "game/city_view.c"),
        new Target(0x429930L, "game/event_city_view.c"),
        new Target(0x450490L, "game/do_city.c"),
        new Target(0x4514f0L, "game/prepare_city_doing.c"),
        new Target(0x451bb0L, "game/do_city_army.c"),
        new Target(0x46a380L, "game/city_army_error_fix.c"),

        new Target(0x43dec0L, "game/diplomat_battle_back.c"),
        new Target(0x443c30L, "game/diplomat_end_battle_back.c"),
        new Target(0x473270L, "game/load_dat.c"),

        new Target(0x405540L, "extra/ai_diplomat.c"),
        new Target(0x430370L, "extra/decode_city.c"),
        new Target(0x431800L, "extra/decode_new_map.c"),
        new Target(0x433020L, "extra/decode_long_wall.c"),
        new Target(0x433810L, "extra/decode_road.c"),
        new Target(0x433da0L, "extra/decode_minimap.c"),
        new Target(0x438490L, "extra/diplomat_go_buy_city.c"),
        new Target(0x4389c0L, "extra/diplomat_ask_surrender.c"),
        new Target(0x438e20L, "extra/diplomat_steal_science.c"),
        new Target(0x4393f0L, "extra/diplomat_scare_monger.c"),
        new Target(0x439880L, "extra/diplomat_crack_build.c"),
        new Target(0x439d70L, "extra/diplomat_commotion.c"),
        new Target(0x43ebf0L, "extra/diplomat_talking.c"),
        new Target(0x43ece0L, "extra/diplomat_answer_cond_check.c"),
        new Target(0x43ee60L, "extra/diplomat_allow.c"),
        new Target(0x43f750L, "extra/diplomat_value.c"),
        new Target(0x440de0L, "extra/diplomat_ask_what.c"),
        new Target(0x441600L, "extra/diplomat_ask_check.c"),
        new Target(0x442430L, "extra/diplomat_compare.c"),
        new Target(0x442aa0L, "extra/reflash_dip_city_list.c"),
        new Target(0x44ad80L, "extra/diplomat_running.c"),
        new Target(0x44b460L, "extra/diplomat_turn.c"),
        new Target(0x42eed0L, "ui/node_insert_data_format.c"),
        new Target(0x42f210L, "ui/node_delete_data_format.c"),
        new Target(0x42f290L, "ui/add_new_data_format.c"),
        new Target(0x42f3e0L, "ui/reflash_data_format.c"),
        new Target(0x42f5c0L, "ui/del_data_format.c"),
        new Target(0x42f600L, "ui/check_press_data_format.c"),
        new Target(0x4578a0L, "editor/before_edit_empire_country.c"),
        new Target(0x456c50L, "editor/after_edit_country.c"),
        new Target(0x458d80L, "editor/mlp_edit_empire_country.c"),
        new Target(0x452110L, "editor/before_edit_army.c"),
        new Target(0x454570L, "editor/before_edit_build.c"),
        new Target(0x45d6f0L, "editor/before_edit_government.c"),
        new Target(0x45e4d0L, "editor/before_edit_ground.c"),
        new Target(0x45ee10L, "editor/before_edit_empire_hero.c"),
        new Target(0x467010L, "editor/before_edit_science_power.c"),
        new Target(0x467250L, "editor/before_edit_science_set.c"),
        new Target(0x467740L, "editor/science_know_with_prerequisites.c"),
        new Target(0x467dc0L, "editor/put_edit_science_exp.c"),
        new Target(0x45c5d0L, "editor/before_edit_empire_flag.c"),
        new Target(0x45c640L, "editor/after_edit_empire_flag.c"),
        new Target(0x45d0d0L, "editor/save_img_flag.c"),
        new Target(0x45d2c0L, "editor/mlp_edit_empire_flag.c"),
        new Target(0x451de0L, "extra/do_map.c"),
        new Target(0x4596a0L, "extra/before_window_edit_file_detail.c"),
        new Target(0x459f90L, "extra/put_edit_file_detail.c"),
        new Target(0x45b1d0L, "extra/mouse_on_edit_sel_custom_map.c"),
        new Target(0x45b2f0L, "extra/mlr_edit_sel_custom_map.c"),
        new Target(0x45c330L, "extra/mouse_on_edit_sel_pcx_file.c"),
        new Target(0x46b850L, "extra/load_ui_string_emg_a.c"),
        new Target(0x46cc70L, "extra/load_ui_string_emg_xmg.c"),
        new Target(0x47b530L, "extra/reflash_city_road.c"),
        new Target(0x47b890L, "extra/make_city_map.c"),
        new Target(0x47be60L, "extra/make_city_wall.c"),
        new Target(0x47c040L, "extra/make_city_culvert.c"),
        new Target(0x47c2a0L, "extra/delete_city_wall_or_culvert.c"),
        new Target(0x47c330L, "extra/make_city_train.c"),
        new Target(0x47c8b0L, "extra/map_to_battle_army.c"),
        new Target(0x477800L, "extra/load_map_gameinfo.c"),
        new Target(0x47e230L, "extra/load_mainmenu_emg.c"),
        new Target(0x47ee50L, "extra/menu_editmenu_init.c"),
        new Target(0x47eef0L, "extra/menu_editmenu_quit.c"),
        new Target(0x47f0a0L, "extra/put_sub_editmenu.c"),
        new Target(0x47f910L, "extra/mlr_newedit.c"),
        new Target(0x4891a0L, "extra/ui_yes_no_dialog_a.c"),
        new Target(0x489580L, "extra/ui_yes_no_dialog_b.c"),
        new Target(0x4896d0L, "extra/ui_yes_no_dialog_c.c"),
        new Target(0x48dc10L, "extra/near_beach_city_found.c"),
        new Target(0x48ded0L, "extra/near_beach_city_with_army_found.c"),
        new Target(0x48e210L, "extra/near_beach_city_cap_army_found.c"),
        new Target(0x48e6a0L, "extra/near_city_with_army_found.c"),
        new Target(0x48e8d0L, "extra/near_city_found_xy.c"),
        new Target(0x48eae0L, "extra/near_city_found_xy_no_land.c"),
        new Target(0x48ec50L, "extra/near_city_found_capable.c"),
        new Target(0x48edd0L, "extra/in_range_near_dest_city_found.c"),
        new Target(0x48efa0L, "extra/near_city_with_air_found.c"),
        new Target(0x48f1e0L, "extra/near_city_away_enemy.c"),
        new Target(0x48f3b0L, "extra/no_dpa_near_city_away_enemy.c"),
        new Target(0x48f620L, "extra/no_dpa_near_city_near_sea.c"),
        new Target(0x48f980L, "extra/near_city_user_know_found.c"),
        new Target(0x48faa0L, "extra/no_dpa_near_city_found.c"),
        new Target(0x48c8f0L, "extra/check_mouse_on_window.c"),
        new Target(0x492760L, "extra/do_country_diplomat.c"),
        new Target(0x495320L, "extra/order_diplomat_choice_mission.c"),
        new Target(0x495780L, "extra/order_diplomat_sel_buy.c"),
        new Target(0x4959a0L, "extra/order_diplomat_sel_take_city_or_diplomat.c"),
        new Target(0x495a50L, "extra/order_diplomat_sel_take_city.c"),
        new Target(0x496df0L, "extra/start_map_battle_from_tile.c"),
        new Target(0x49fd10L, "extra/edit_start.c"),
        new Target(0x49fe50L, "extra/edit_finish.c"),
        new Target(0x49e580L, "extra/put_city_view.c"),
        new Target(0x4b0c00L, "extra/read_keyboard.c"),
        new Target(0x4b3330L, "extra/read_mlp_edit.c"),
        new Target(0x4b6d70L, "extra/mlr_edit_gamemap.c"),
        new Target(0x4b80c0L, "extra/read_mrp_edit.c"),
        new Target(0x4b8db0L, "extra/read_mrr_edit.c"),
        new Target(0x4b8820L, "editor/clear_mountain.c"),
        new Target(0x4b8f60L, "editor/cancel_all_army_on_tile.c"),
        new Target(0x4bc720L, "extra/playgame_init.c"),
        new Target(0x4d91a0L, "extra/put_city_citizen.c"),
        new Target(0x4df2e0L, "extra/put_city_make.c"),
        new Target(0x4ec1a0L, "extra/load_ui_dip_emg.c")
    };

    private static final String[] STRING_HINTS = new String[] {
        "Battle:",
        "Battle_",
        "City_",
        "City_View",
        "Diplomat",
        "Decode_",
        "Load_Dat",
        "Do_City",
        "Do_Map",
        "MAINMENU",
        "UI_"
    };

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("usage: GhidraExport.java <out_dir> [--all-functions]");
        }
        File outRoot = new File(args[0]).getAbsoluteFile();
        boolean allFunctions = false;
        for (int i = 1; i < args.length; i++) {
            if ("--all-functions".equals(args[i])) {
                allFunctions = true;
            }
        }
        mkdirs(outRoot);

        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        for (Target target : TARGETS) {
            writeFunction(ifc, outRoot, target);
        }
        if (allFunctions) {
            writeAllFunctions(ifc, outRoot);
        }
        writeInventory(outRoot);
        writeStringXrefs(outRoot);
    }

    private void mkdirs(File file) throws Exception {
        if (!file.exists() && !file.mkdirs()) {
            throw new Exception("failed to create " + file);
        }
    }

    private Address addr(long va) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
    }

    private Function functionAtOrContaining(long va) {
        Address address = addr(va);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        return fn;
    }

    private void writeFunction(DecompInterface ifc, File outRoot, Target target) throws Exception {
        File out = new File(outRoot, target.path);
        mkdirs(out.getParentFile());
        PrintWriter writer = new PrintWriter(new FileWriter(out));
        try {
            writer.println("/*");
            writer.println(" * Generated by Ghidra headless decompiler from " + currentProgram.getName() + ".");
            writer.printf(" * Address request: 0x%08x%n", target.va);
            writer.println(" * This is reconstructed pseudocode, not original source.");
            writer.println(" */");
            writer.println();

            Function fn = functionAtOrContaining(target.va);
            if (fn == null) {
                writer.printf("/* No Ghidra function found at or containing 0x%08x. */%n", target.va);
                return;
            }

            DecompileResults result = ifc.decompileFunction(fn, 90, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                writer.print(result.getDecompiledFunction().getC());
            }
            else {
                writer.println("/* Decompile failed for " + fn.getName() + " at " + fn.getEntryPoint() + ". */");
            }
        }
        finally {
            writer.close();
        }
    }

    private void writeAllFunctions(DecompInterface ifc, File outRoot) throws Exception {
        File allRoot = new File(outRoot, "all_functions");
        mkdirs(allRoot);

        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Function fn = it.next();
            String entry = fn.getEntryPoint().toString();
            File out = new File(allRoot, "0x" + entry + "_" + safeFileName(fn.getName()) + ".c");
            writeFunctionObject(ifc, out, fn);
        }
    }

    private void writeFunctionObject(DecompInterface ifc, File out, Function fn) throws Exception {
        mkdirs(out.getParentFile());
        PrintWriter writer = new PrintWriter(new FileWriter(out));
        try {
            writer.println("/*");
            writer.println(" * Generated by Ghidra headless decompiler from " + currentProgram.getName() + ".");
            writer.println(" * Function: " + fn.getName() + " at 0x" + fn.getEntryPoint());
            writer.println(" * This is reconstructed pseudocode, not original source.");
            writer.println(" */");
            writer.println();

            DecompileResults result = ifc.decompileFunction(fn, 90, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                writer.print(result.getDecompiledFunction().getC());
            }
            else {
                writer.println("/* Decompile failed for " + fn.getName() + " at " + fn.getEntryPoint() + ". */");
            }
        }
        finally {
            writer.close();
        }
    }

    private void writeInventory(File outRoot) throws Exception {
        File out = new File(outRoot, "function_inventory.md");
        PrintWriter writer = new PrintWriter(new FileWriter(out));
        try {
            writer.println("# Ghidra Function Inventory");
            writer.println();
            writer.println("Generated from `" + currentProgram.getName() + "`.");
            writer.println();
            writer.println("| Address | Name | Size | Called functions |");
            writer.println("|---:|---|---:|---:|");
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Function fn = it.next();
                int callCount = fn.getCalledFunctions(monitor).size();
                writer.printf("| `0x%s` | `%s` | %d | %d |%n",
                    fn.getEntryPoint(), fn.getName(), fn.getBody().getNumAddresses(), callCount);
            }
        }
        finally {
            writer.close();
        }
    }

    private void writeStringXrefs(File outRoot) throws Exception {
        File out = new File(outRoot, "string_xrefs.md");
        PrintWriter writer = new PrintWriter(new FileWriter(out));
        try {
            writer.println("# String Cross References");
            writer.println();
            writer.println("| Hint | String | Referrer | Function |");
            writer.println("|---|---|---:|---|");
            Set<String> seen = new HashSet<String>();
            Data data = firstDefinedData();
            while (data != null && !monitor.isCancelled()) {
                String value = getStringValue(data);
                if (value != null) {
                    for (String hint : STRING_HINTS) {
                        if (value.indexOf(hint) >= 0) {
                            Reference[] refs = getReferencesTo(data.getAddress());
                            for (Reference ref : refs) {
                                Function fn = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                                String fnName = fn == null ? "" : fn.getName();
                                String key = hint + "\t" + value + "\t" + ref.getFromAddress() + "\t" + fnName;
                                if (seen.add(key)) {
                                    writer.printf("| `%s` | `%s` | `0x%s` | `%s` |%n",
                                        escapeMd(hint), escapeMd(value), ref.getFromAddress(), escapeMd(fnName));
                                }
                            }
                        }
                    }
                }
                data = definedDataAfter(data);
            }
        }
        finally {
            writer.close();
        }
    }

    private Data firstDefinedData() {
        if (!currentProgram.getListing().getDefinedData(true).hasNext()) {
            return null;
        }
        return currentProgram.getListing().getDefinedData(true).next();
    }

    private Data definedDataAfter(Data data) {
        return currentProgram.getListing().getDefinedDataAfter(data.getAddress());
    }

    private String getStringValue(Data data) {
        try {
            StringDataInstance sdi = StringDataInstance.getStringDataInstance(data);
            if (sdi != null && StringDataInstance.isString(data)) {
                return sdi.getStringValue();
            }
        }
        catch (Exception ignored) {
        }
        return null;
    }

    private String escapeMd(String value) {
        return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n");
    }

    private String safeFileName(String value) {
        return value.replaceAll("[^A-Za-z0-9_.-]", "_");
    }
}

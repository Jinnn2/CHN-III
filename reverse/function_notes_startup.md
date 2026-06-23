# Startup Function Notes

These notes track the startup/init module at the function level. Each entry
records the useful triad for reverse work: globals read, globals written, and
key calls. Status/confidence mirrors `function_status.md`.

## Function `0x00420820` - `App_WinMain_Entry`

## Status

partial, 85%

## Inputs

- WinMain-style `HINSTANCE`, previous instance, command line/show parameter
  values. The decompiler signature is still generic.

## Globals Read

- `g_editor_mode_enabled`
- `g_commandline_load_exception_flag`
- `g_commandline_demo_mode_enabled`
- `g_directdraw_ready`
- `g_app_screen_state`

## Globals Written

- `g_app_instance`
- `g_single_instance_mutex`
- `g_app_screen_state`
- `g_present_use_blt_mode`
- `g_menu_action_tick`
- `g_frame_tick`
- `DAT_0074d348` frame tick baseline

## Calls

- `CreateMutexA`, `GetLastError`
- `Process_CommandLine_Args`
- `Create_Main_Window`
- `Init_Working_Directories`
- `Init_SetUp`
- `Get_Game_Tick`
- `PeekMessageA`, `WaitMessage`, `TranslateMessage`, `DispatchMessageA`
- `Game_Frame_Pump` when `g_app_screen_state == 0x25`
- `App_Frame_Pump` otherwise

## Observations

- Uses mutex name `CHINA2` and exits when another instance exists.
- Initializes app screen state to main-menu/default flow, then switches to
  state `0x24` for editor, command-line load, or demo startup.
- The main loop is a standard idle pump: process Windows messages when present;
  otherwise wait if DirectDraw is not ready or run the appropriate frame pump.

## Function `0x00420350` - `Create_Main_Window`

## Status

partial, 80%

## Inputs

- `nCmdShow`-like show-window value.

## Globals Read

- `g_app_instance`
- `g_present_use_blt_mode`

## Globals Written

- `g_main_window`

## Calls

- `RegisterClassExA`
- `LoadIconA`, `LoadCursorA`, `GetStockObject`
- `GetSystemMetrics`
- `CreateWindowExA`
- `ShowWindow`, `UpdateWindow`, `SetFocus`, `ShowCursor`

## Observations

- Registers the main class/window title from the same string at `0x005153dc`.
- Uses wndproc `Main_WindowProc`; this is the startup/input bridge into Win32
  messages.
- Creates a screen-sized host window. `g_present_use_blt_mode == 0` sets
  extended style `8`; otherwise the extended style is `0`.

## Function `0x004204b0` - `Init_Working_Directories`

## Status

partial, 80%

## Inputs

- None direct.

## Globals Read

- Startup/current directory buffer at `g_startup_work_dir`.
- Static suffix strings for resource/data subdirectories.

## Globals Written

- `g_startup_work_dir`
- `DAT_00771c10`
- `DAT_0076122c`
- `DAT_00761128`
- `DAT_00771d94`
- `DAT_00761330`
- `DAT_00748e3c`
- `g_map_data_dir`
- `DAT_0074a10c`
- `DAT_00748da8`
- `DAT_0075525c`

## Calls

- `Trace_Function("SetWorkDirectory")`
- CRT/string helpers for path copy/concatenation.

## Observations

- Normalizes the executable/current directory by trimming one trailing slash.
- Builds a family of absolute resource directories from the work directory.
- `g_map_data_dir` is later used by `Init_SetUp` when probing `EXCEPTION.MAP`
  and related exception scenario files.

## Function `0x0040b450` - `Process_CommandLine_Args`

## Status

partial, 80%

## Globals Read

- Command line from `GetCommandLineA`.

## Globals Written

- `DAT_0075593d` server-related flag
- `DAT_00755904` server/no-local or mode flag
- `g_commandline_load_exception_flag`
- `g_commandline_demo_mode_enabled`
- `DAT_00755974` language/simple mode
- `DAT_0075594c` tutorial/teach enable flag
- `g_editor_mode_enabled`
- `DAT_005d9198`
- `DAT_005d9199`

## Calls

- `Trace_Function("Argument_Process")`
- `GetCommandLineA`
- CRT `_strstr`-style option checks.

## Observations

- Recognized strings include `SERVER`, `LOAD`, `DEMO`, `SIMPLE`, `ENGLISH`,
  `NOTEACH`, `EDIT`, `VIVIAN`, and one currently unnamed short/debug option.
- This is a reliable navigation point for startup modes, including map editor
  entry.

## Function `0x0046e950` - `Init_SetUp`

## Status

partial, 85%

## Globals Read

- `g_main_window`
- `g_app_instance`
- `g_present_use_blt_mode`
- `g_commandline_load_exception_flag`
- `g_client_width`
- `g_client_height`
- `g_map_data_dir`

## Globals Written

- `g_resolution_mode_index`
- base EMG/IMG resource handles such as edit image, metal/new UI/mouse/UI
- `g_request_redraw`
- `DAT_00755988` loading TMG background
- `g_commandline_load_exception_flag` can be set by exception-map prompt

## Calls

- debug trace/file reset helpers
- input/window helper initialization
- `Init_DirectDraw_Runtime`
- font/input helpers
- `Apply_Resolution_Mode`
- AVI player helper for `.\ANIM\LOGO_FINAL.AVI` and `.\ANIM\FINAL.AVI`
- `Set_Color`
- `Safe_LoadIMG`, `Load_EMG_Resource`
- font availability/install helpers for `PMingLiU` and `SimSun`
- `Load_TMG_Background("Loading")`
- `Draw_Image_To_Backbuffer`, `Present_Dirty_Rects`
- exception map probe and `UI_YesNo_Dialog`
- music/CD initialization helpers

## Observations

- This is the broad bootstrap resource loader after the window and working
  directories exist.
- It draws the loading TMG after the initial UI/font setup.
- It probes `EXCEPTION.MAP`; if present, prompts the user to load or delete
  exception scenario files (`EXCEPTION.MGI`, `.CTN`, `.LDN`, `.GRP`).
- It optionally initializes music if not in the server/no-local mode.

## Function `0x0041f9a0` - `App_Frame_Pump`

## Status

partial, 80%

## Globals Read

- `g_frame_tick`
- `g_menu_action_tick`
- redraw-throttle globals around `DAT_007350aa`

## Globals Written

- `g_frame_tick`
- `g_request_redraw`
- `g_frame_elapsed_ms_accum`
- `g_frame_count_this_second`
- `g_frame_count_last_second`
- `g_frame_one_second_elapsed`
- `g_menu_action_tick`

## Calls

- `Get_Game_Tick`
- input/mouse helpers
- `Read_Keyboard`
- draw/update helpers
- `Present_Dirty_Rects`

## Observations

- This is the non-game idle pump used for menu/dialog flows.
- It updates timing, samples input, asks `Read_Keyboard` to dispatch, then
  either redraws and presents or only presents.

## Function `0x0041fab0` - `Game_Frame_Pump`

## Status

partial, 80%

## Globals Read

- `g_current_map_scenario_info.auto_city_processing_countdown`
- `g_scripted_start_mode_enabled`
- `g_request_redraw`
- several map UI/cursor state globals still unnamed

## Globals Written

- `g_frame_tick`
- `g_request_redraw`
- `g_frame_elapsed_ms_accum`
- `g_frame_count_this_second`
- `g_frame_count_last_second`
- `g_frame_one_second_elapsed`
- `g_current_map_scenario_info.auto_city_processing_countdown`
- map blink/redraw cadence flags

## Calls

- `Get_Game_Tick`
- input/mouse helpers
- `Read_Keyboard`
- `Prepare_City_Doing`
- map/UI redraw helpers
- `Present_Dirty_Rects`

## Observations

- This is the in-game/map/editor idle pump used when state is `0x25`.
- Once per second it adjusts a frame-delay value and decrements automatic city
  processing countdown; when enabled and expired it calls `Prepare_City_Doing`.
- It also owns a blink/redraw cadence and conditionally skips `Read_Keyboard`
  during scripted startup unless the relevant script entry is ready.

## Function `0x004c60a0` - `ShutDown_Game`

## Status

partial, 80%

## Globals Read/Written

- Frees map buffers, minimap buffer, land-record buffers, color/fade tables,
  dark table, edit brush buffers, loaded TMG backgrounds, IMG/EMG banks, and
  music/window/input resources.
- Writes `CONFIG.DAT` from config blocks and `KEYDEF.DAT` from key bindings.

## Calls

- `Clear_All_Memory`
- allocation/free helper `FUN_0047de70`
- `CreateFileA`, `WriteFile`, `CloseHandle`
- `CloseIndexIMG`, `Free_EMG_Base`, `Safe_FreeIMG`, `Free_EMG_Resource`
- platform/window/input teardown helpers

## Observations

- This is the broad application teardown counterpart to `Init_SetUp`.
- It is also a useful inventory of long-lived runtime buffers.

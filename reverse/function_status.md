# Function Status

This is the working function-status board. It is intentionally smaller than
`ghidra_export/function_inventory.md`: track functions here when they become
useful navigation points or have a real semantic guess.

Status values: `raw`, `named`, `candidate`, `partial`, `stable`.

| Address | Current Name | Status | Module | Confidence | Notes |
|---|---|---|---|---:|---|
| `0x00401000` | `AI_ActShip` | named | ai_orders | 40% | Name from trace string/annotation; naval action handler family. |
| `0x00403520` | `AI_Army` | named | ai_orders | 40% | Name from trace string; called by idle/order dispatch. |
| `0x00405540` | `AI_Diplomat` | named | diplomacy_country | 40% | Name from trace string and diplomacy xrefs. |
| `0x00406ff0` | `AI_Ship` | named | ai_orders | 40% | Name from trace string; ship AI executor. |
| `0x004086e0` | `NewLand_Name` | partial | map | 70% | Promotes/updates named-point rows loaded by `Load_Dat`. |
| `0x0040b450` | `Process_CommandLine_Args` | partial | startup_init | 80% | Parses `SERVER`, `LOAD`, `DEMO`, `SIMPLE`, `ENGLISH`, `NOTEACH`, `EDIT`, and hidden/debug flags. |
| `0x0040b580` | `Start_Map_Battle_From_Army` | partial | battle | 65% | Battle-entry path from active map army; paired with tile entry path. |
| `0x00411ea0` | `City_Capture_Transfer` | partial | city_economy | 65% | Transfers city ownership and related state after capture. |
| `0x00414b70` | `Battle_Peace_Place` | named | battle | 45% | Name from trace string; battle placement helper. |
| `0x00414c50` | `Battle_First_Line` | named | battle | 45% | Name from trace string; battle formation helper. |
| `0x00415600` | `Battle_AutoArrange` | partial | battle | 65% | Arranges battle units using side counts and battle grid state. |
| `0x00415cb0` | `Do_Battle_Army_And_Battle_Die` | partial | battle | 65% | Main battle/unit death routine; large and not field-complete. |
| `0x00418510` | `Prepare_Battle_Tile_Object_Flags` | partial | battle | 65% | Derives object/city-present flags from source map tiles. |
| `0x00418830` | `BattleArmy` | partial | battle | 70% | Expands source map armies into battle-side unit records. |
| `0x004189c0` | `Decode_Battle` | named | battle | 50% | Name from trace string; battle map redraw/decode path. |
| `0x00419240` | `Make_Battle_Map` | partial | battle | 65% | Chooses/builds battle map from source tile/unit classes. |
| `0x00419f30` | `Battle_Arrange_Position` | partial | battle | 60% | Loads `UI_BATTLE.EMG` and positions battle UI/units. |
| `0x0041a9f0` | `City_Belong_Change` | partial | city_economy | 70% | Changes city owner and visibility/country accounting. |
| `0x0041b0f0` | `Army_Belong_Change` | partial | ai_orders | 70% | Changes army owner and related country/city visibility state. |
| `0x0041b4a0` | `Bridge_Able` | named | map | 50% | Terrain/improvement predicate; evidence from editor/map work. |
| `0x0041b6c0` | `Irrigate_Able` | named | map | 50% | Terrain improvement predicate. |
| `0x0041b960` | `Resource_Able` | partial | map | 75% | Validates resource id against tile terrain and battle-feature table. |
| `0x0041daf0` | `UserSet_City_Resource` | named | city_economy | 50% | City resource assignment/update path. |
| `0x0041dea0` | `Cal_City_JobPeople` | named | city_economy | 55% | City worker/job calculation; name from trace string. |
| `0x0041e200` | `Cal_City_Resource` | partial | city_economy | 70% | Reads city resource defs and tile resource/feature fields. |
| `0x0041f9a0` | `App_Frame_Pump` | partial | startup_init | 80% | Non-game idle frame pump: timing, input, redraw flag, draw/present. |
| `0x0041fab0` | `Game_Frame_Pump` | partial | startup_init | 80% | Game/editor idle frame pump: timing throttle, blink/redraw cadence, input, auto city processing. |
| `0x0041fd60` | `Main_WindowProc` | partial | input | 80% | Main Win32 message bridge: lifecycle, activation, keyboard, mouse, IME, timer, custom redraw/restore message. |
| `0x00420350` | `Create_Main_Window` | partial | startup_init | 80% | Registers main window class, creates fullscreen/borderless host window, hides cursor. |
| `0x004204b0` | `Init_Working_Directories` | partial | startup_init | 80% | Builds canonical work/resource path strings from startup directory. |
| `0x00420820` | `App_WinMain_Entry` | partial | startup_init | 85% | WinMain-like entry: mutex, command line, window/path/setup, screen-state loop, message dispatch. |
| `0x00420a30` | `Font_Select` | named | render_ui | 55% | Font selection helper. |
| `0x00420ba0` | `Draw_Text_Centered` | named | render_ui | 60% | Text draw helper. |
| `0x00420c00` | `Draw_Text` | named | render_ui | 60% | Text draw helper. |
| `0x00425940` | `City_Manager` | partial | city_economy | 60% | Loads `UI_CITY.EMG` and enters city UI/management path. |
| `0x00430370` | `Decode_City` | named | map | 50% | Name from trace string; city tile decode/redraw. |
| `0x00431800` | `Decode_NewMap` | partial | map | 75% | Large map redraw/decode path using tile buffer and editor flag. |
| `0x00433020` | `Decode_LongWall` | partial | map | 70% | Decodes long-wall adjacency/sprites using hex neighbor tables. |
| `0x00433810` | `Decode_Road` | partial | map | 70% | Decodes road/bridge adjacency/sprites using hex neighbor tables. |
| `0x00433da0` | `Decode_MiniMap` | named | map | 55% | Minimap decode/redraw path; called after load and map changes. |
| `0x00438490` | `Diplomat_Go_Buy_City` | named | diplomacy_country | 45% | Name from trace string; diplomacy action. |
| `0x0043dec0` | `Diplomat_Start` | named | diplomacy_country | 45% | Name from trace string; loads/enters diplomacy UI. |
| `0x00450490` | `Do_City` | partial | city_economy | 70% | Iterates current city turn/update state and city linked list. |
| `0x00451de0` | `Do_Map` | partial | map | 65% | Map/gameplay top-level update path. |
| `0x00452110` | `Before_Edit_Army` | partial | editor_data | 75% | Backs up and binds `ArmyTypeDef_0x400`; checks `ARMYBASE.DAT`. |
| `0x00454570` | `Before_Edit_Build` | partial | editor_data | 75% | Backs up and binds `BuildingDef_0x200`; checks `BUILD.DAT`. |
| `0x004578a0` | `Before_Edit_Empire_Country` | partial | editor_data | 75% | Reads/writes `EMPIRE.DAT` and editor backup table. |
| `0x0045d6f0` | `Before_Edit_Goverment` | partial | editor_data | 70% | Backs up and binds `GovernmentDef_0x74`; checks `GOVERMENT.DAT`. |
| `0x0045e4d0` | `Before_Edit_Ground` | partial | editor_data | 75% | Backs up and binds `GroundDef_0x24`; checks `GROUND.DAT`. |
| `0x0045ee10` | `Before_Edit_Empire_Hero` | partial | editor_data | 75% | Reads/writes `HERO.DAT`; previews `DIP_%02d` resources. |
| `0x00467010` | `Before_Edit_Science_Power` | partial | editor_data | 70% | Backs up science priority target table. |
| `0x00467250` | `Before_Edit_Science_Set` | partial | editor_data | 70% | Edits science known/prerequisite status for country. |
| `0x0046b850` | `Load_UI_String_EMG` | partial | file_io | 70% | Loads `UI_STRING.EMG` and score-list background. |
| `0x0046cc70` | `Load_UI_String_EMG_XMG` | partial | file_io | 70% | Loads `UI_STRING.EMG` plus `UI_STRING.XMG`; score/history path. |
| `0x0046d310` | `Init_DirectDraw_Runtime` | partial | render_ui | 80% | DirectDraw create/query/cooperative-level/surface setup. |
| `0x0046e950` | `Init_SetUp` | partial | startup_init | 85% | Main setup: DirectDraw, AVI intro, base UI resources, fonts, loading TMG, exception map prompt, music. |
| `0x00473270` | `Load_Dat` | partial | file_io | 75% | Large scenario/save/table loader; reconstructs map/city/army/country state. |
| `0x00477800` | `Load_Map_GameInfo` | named | file_io | 55% | Map/game info loader from string-derived name. |
| `0x00477ff0` | `Load_EMG_Base` | partial | file_io | 75% | Loads long-lived EMG/XMG/IMG resources and color/fade caches. |
| `0x004789e0` | `Load_EMG_Resource` | partial | file_io | 75% | Safe wrapper around EMG load; resource path and trace strings verified. |
| `0x00478a50` | `Safe_LoadIMG` | named | file_io | 65% | IMG loader wrapper; used for flags and indexed portraits. |
| `0x00478ac0` | `Load_XMG_Resource` | partial | file_io | 75% | Safe wrapper around XMG load. |
| `0x00478eb0` | `MainMenu_Init` | partial | render_ui | 75% | Loads main menu TMG/EMG/XMG and initializes menu state. |
| `0x00479000` | `MainMenu_Quit` | partial | render_ui | 70% | Frees main menu EMG/XMG resources. |
| `0x00479040` | `PutScreen_Mainmenu` | partial | render_ui | 65% | Main menu draw/animation path. |
| `0x00479420` | `MLR_MainMenu` | partial | render_ui | 65% | Main menu mouse-left-release handler. |
| `0x0047b530` | `Reflash_City_Road` | named | map | 55% | City-road redraw/update helper. |
| `0x0047b890` | `Make_City_Map` | partial | map | 65% | Builds/updates city map overlays. |
| `0x0047c8b0` | `Map_To_Battle_Army` | partial | battle | 70% | Converts map tile occupants into battle units and feature bonuses. |
| `0x0047e230` | `Load_MAINMENU_EMG` | partial | file_io | 70% | Loads `MAINMENU.EMG` and background. |
| `0x0047ee50` | `Menu_EditMenu_Init` | partial | editor_map | 65% | Initializes map editor menu/background. |
| `0x0047f910` | `MLR_NewEdit` | candidate | editor_map | 60% | New-map/edit menu click path. |
| `0x004891a0` | `UI_YesNo_Dialog` | named | render_ui | 55% | Confirmation dialog using `UI_YN.EMG`. |
| `0x004912e0` | `Do_Army_TurnJob` | partial | ai_orders | 70% | Advances map work/improvement jobs and completion effects. |
| `0x004939c0` | `Clear_Forest_Or_Resource` | partial | map | 70% | Clears feature/resource state and grants resource value. |
| `0x00493be0` | `Make_New_Make` | partial | map | 65% | Completes/updates tile improvement state. |
| `0x00499090` | `Apply_OrderQueue_Army` | partial | ai_orders | 70% | Core unit order-state applier. |
| `0x0049bec0` | `Load_TMG_Background` | partial | file_io | 80% | Opens `GRAPH\<name>.TMG`, reads image/header, creates decoded background. |
| `0x0049fd10` | `Edit_Start` | partial | editor_map | 75% | Allocates editor map backup and enters edit state. |
| `0x0049fe50` | `Edit_Finish` | partial | editor_map | 75% | Frees editor backups and reloads/commits edited data resources. |
| `0x004b0c00` | `Read_Keyboard` | partial | input | 75% | Frame-level keyboard dispatcher: directions, map bookmarks, city entry, editor toggle/undo, and army order bridge. |
| `0x004b3330` | `Read_MLP_Edit` | partial | editor_map | 75% | Editor left-press/drag handler; paints terrain/resources/ownership/names. |
| `0x004b6d70` | `MLR_Edit_GameMap` | partial | editor_map | 75% | Editor mouse-left-release on map; creates city/army/name/resource entries. |
| `0x004b80c0` | `Read_MRP_Edit` | partial | editor_map | 75% | Editor right-press handler; clears/removes map objects and fields. |
| `0x004b8db0` | `Read_MRR_Edit` | partial | editor_map | 70% | Editor right-release handler; clears named-point rows. |
| `0x004c2da0` | `Apply_Resolution_Mode` | partial | render_ui | 80% | Applies logical resolution state and viewport offsets. |
| `0x004c60a0` | `ShutDown_Game` | partial | startup_init | 80% | Frees dynamic map/render/resource buffers, writes `CONFIG.DAT`/`KEYDEF.DAT`, releases IMG/EMG and platform state. |
| `0x004c6e60` | `DiagCoords_To_TileX` | named | map | 65% | Tile/diagnonal coordinate conversion helper. |
| `0x004c7160` | `Tile_Direction_DeltaX` | named | map | 65% | Tile direction delta helper. |
| `0x004d2cc0` | `TestRoad` | partial | ai_orders | 70% | Pathfinding/route validation for army orders. |
| `0x004ec1a0` | `Load_UI_DIP_EMG` | partial | file_io | 70% | Diplomacy UI resource/background load path. |
| `0x004f0030` | `Lock_Back_Surface` | partial | render_ui | 80% | DirectDraw back-surface lock and pitch/pointer state. |
| `0x004f0070` | `Unlock_Back_Surface` | partial | render_ui | 80% | DirectDraw back-surface unlock. |
| `0x004f02d0` | `Present_Dirty_Rects` | partial | render_ui | 80% | Dirty-rect present path using DirectDraw surface blits. |
| `0x004f0afd` | `Set_Display_Mode_From_Mode_Table` | partial | render_ui | 75% | Uses display mode width/height tables and DirectDraw `SetDisplayMode`. |
| `0x004f0ce0` | `Create_Front_Surface` | partial | render_ui | 75% | Creates primary/front DirectDraw surface. |
| `0x004f0de0` | `Create_Back_Surface` | partial | render_ui | 75% | Creates CPU-drawn back/logical surface. |
| `0x004f4f60` | `Init_Pixel_Format_Tables` | candidate | render_ui | 65% | Builds pixel conversion/color lookup support tables. |
| `0x004f81e0` | `Init_Surface_Pixel_State` | partial | render_ui | 75% | Reads surface desc/pixel format and initializes render globals. |
| `0x005027b0` | `Input_On_KeyDown` | partial | input | 80% | Handles `WM_KEYDOWN`/`WM_SYSKEYDOWN`, updates modifier flags and queues key-down events. |
| `0x005028b0` | `Input_On_KeyUp` | partial | input | 80% | Handles `WM_KEYUP`/`WM_SYSKEYUP`, clears key state and queues key-up events. |
| `0x00502a00` | `Input_Reset_Keyboard_State` | partial | input | 80% | Sets focus, clears key bitmap, and resets keyboard ring indices. |
| `0x00502a40` | `Input_Is_KeyDownOrModifier` | partial | input | 85% | Queries Shift/Ctrl/Alt aliases from modifier bits or ordinary key-down bitmap bytes. |
| `0x00502b00` | `Input_Pop_KeyEvent_candidate` | partial | input | 80% | Pops translated key code and event type from 64-slot keyboard event ring. |
| `0x00502b60` | `Input_Release_IME_Resources_candidate` | candidate | input | 65% | Releases input/IME object and two allocated buffers. |
| `0x00502bc0` | `Input_Create_IME_Context_candidate` | candidate | input | 70% | Creates and associates an IME context for the window. |
| `0x00502bf0` | `Input_Reassociate_IME_Context_candidate` | candidate | input | 70% | Reassociates saved IME context when present. |
| `0x00502c70` | `Input_On_InputLangChange_candidate` | candidate | input | 65% | Handles `WM_INPUTLANGCHANGE`; probes IME/keyboard layout registry text and posts status update. |
| `0x00502fd0` | `IME_On_Composition_candidate` | candidate | input | 65% | Handles `WM_IME_COMPOSITION`; reads composition/result strings and feeds committed bytes into char queue. |
| `0x00503360` | `Input_On_MouseButtonDown` | partial | input | 80% | Queues mouse down events with button id and lParam x/y coordinates. |
| `0x005033f0` | `Input_On_MouseButtonUp` | partial | input | 80% | Queues mouse up events with button id and lParam x/y coordinates. |
| `0x00503480` | `Input_On_MouseMove` | partial | input | 75% | Tracks mouse x/y, clamps to capture bounds, recenters cursor if outside bounds. |
| `0x00503710` | `Input_Set_MouseCapture` | named | input | 75% | Wraps `SetCapture`/`ReleaseCapture` and writes the mouse-capture flag. |
| `0x00503730` | `Format_Text` | named | render_ui | 60% | Formatting helper used by resource loaders and UI. |
| `0x00405b70` | `FUN_00405b70` | raw | unknown | 0% | Untouched large function; keep in inventory until xrefs explain it. |
| `0x0040da80` | `FUN_0040da80` | raw | unknown | 0% | Untouched large function; likely important due size/call count, but no safe name yet. |
| `0x0041bf20` | `FUN_0041bf20` | raw | unknown | 0% | Untouched large function near city/resource predicates. |

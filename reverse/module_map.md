# Module Map

This file is the navigation map for the restored executable. It groups
functions by where to start reading, not by original source-file boundaries.
Use `function_status.md` for per-function confidence and next actions.

## Startup / Init

- `0x00420820` `App_WinMain_Entry`: WinMain-like entry and screen-state loop.
- `0x0041f9a0` `App_Frame_Pump`: top-level message/frame pump.
- `0x0041fab0` `Game_Frame_Pump`: in-game/editor frame pump.
- `0x0040b450` `Process_CommandLine_Args`: editor/demo/load flags.
- `0x00420350` `Create_Main_Window`: registers the window class and creates the main host window.
- `0x004204b0` `Init_Working_Directories`: derives work/resource directory strings used by loaders.
- `0x0046e950` `Init_SetUp`: DirectDraw, fonts, base resources, startup data.
- `0x004c60a0` `ShutDown_Game`: config/key save, resource release, DirectDraw/window shutdown.
- `0x004c6490` `Clear_All_Memory`: cleanup/reset support.

## File IO

- `0x00473270` `Load_Dat`: large DAT/save/scenario loader.
- `0x00477800` `Load_Map_GameInfo`: map metadata/game-info loader.
- `0x00477ff0` `Load_EMG_Base`: long-lived EMG/XMG/IMG resources and lookup-cache DAT files.
- `0x004789e0` `Load_EMG_Resource`: safe EMG wrapper.
- `0x00478ac0` `Load_XMG_Resource`: safe XMG wrapper.
- `0x00478a50` `Safe_LoadIMG`: IMG loader wrapper.
- `0x00478b30` `Free_EMG_Resource`, `0x00478b90` `Free_XMG_Resource`, `0x00478b60` `Safe_FreeIMG`.
- `0x0049bec0` `Load_TMG_Background`: `GRAPH\<name>.TMG` background loader.
- `0x0046b850` `Load_UI_String_EMG`, `0x0046cc70` `Load_UI_String_EMG_XMG`.
- `0x0047e230` `Load_MAINMENU_EMG`.
- `0x004ec1a0` `Load_UI_DIP_EMG`.
- Editor table file touchpoints: `Before_Edit_Army`, `Before_Edit_Build`, `Before_Edit_Empire_Country`, `Before_Edit_Goverment`, `Before_Edit_Ground`, `Before_Edit_Empire_Hero`, `Save_IMG_Flag`.

## Render / UI

- DirectDraw setup: `0x0046d310` `Init_DirectDraw_Runtime`.
- Surface lifecycle: `Create_Front_Surface`, `Create_Back_Surface`, `Lock_Back_Surface`, `Unlock_Back_Surface`.
- Present path: `0x004f02d0` `Present_Dirty_Rects`.
- Resolution/pixel state: `Apply_Resolution_Mode`, `Set_Display_Mode_From_Mode_Table`, `Init_Surface_Pixel_State`, `Init_Pixel_Format_Tables`.
- Text/UI helpers: `Font_Select`, `Draw_Text`, `Draw_Text_Centered`, `Format_Text`, `UI_YesNo_Dialog`.
- Main menu: `MainMenu_Init`, `PutScreen_Mainmenu`, `MLR_MainMenu`, `MainMenu_Quit`, `Load_MAINMENU_EMG`.
- Data-format UI list: `NodeInsert_DataFormat`, `NodeDelete_DataFormat`, `Add_New_DataFormat`, `Reflash_DataFormat`, `Del_DataFormat`, `CheckPress_DataFormat`.

## Input

- `0x0041fd60` `Main_WindowProc`: Win32 message bridge installed by `Create_Main_Window`.
- `0x005027b0` `Input_On_KeyDown` / `0x005028b0` `Input_On_KeyUp`: keyboard event queue and modifier state.
- `0x00502a00` `Input_Reset_Keyboard_State`: focus/reset helper that clears key state and keyboard ring indices.
- `0x00502a40` `Input_Is_KeyDownOrModifier`: key bitmap and Shift/Ctrl/Alt alias query.
- `0x00502b00` `Input_Pop_KeyEvent_candidate`: 64-slot keyboard event ring popper used by frame pumps, dialogs, and text entry.
- `0x00503360` `Input_On_MouseButtonDown` / `0x005033f0` `Input_On_MouseButtonUp`: mouse button event queue.
- `0x00503480` `Input_On_MouseMove`: mouse coordinate/capture clamp.
- `0x00503710` `Input_Set_MouseCapture`: `SetCapture`/`ReleaseCapture` wrapper.
- IME/layout bridge: `Input_Create_IME_Context_candidate`, `Input_Reassociate_IME_Context_candidate`, `Input_On_InputLangChange_candidate`, `IME_On_Composition_candidate`, `Input_Release_IME_Resources_candidate`.
- `0x004b0c00` `Read_Keyboard`: frame-level keyboard dispatch for map directions/repeat, map bookmarks, selected-city entry, editor toggle/undo, debug chords, and active-army route/order targeting.
- Mouse-left release handlers use `MLR_` prefix: `MLR_MainMenu`, `MLR_NewEdit`, `MLR_Edit_GameMap`, `MLR_Edit_SelCustomMap`.
- Editor press/release handlers: `Read_MLP_Edit`, `Read_MRP_Edit`, `Read_MRR_Edit`.
- `CheckMouseOnWindow` and `MouseOn_Edit_*` helpers are UI hit-test anchors.

## Map

- Tile coordinate helpers: `DiagCoords_To_TileX/Y`, `Tile_To_DiagCoordA/B`, `Tile_Direction_DeltaX/Y`, `Tile_Distance_With_Wrap`.
- Decode/redraw: `Decode_NewMap`, `Decode_City`, `Decode_LongWall`, `Decode_Road`, `Decode_MiniMap`.
- Tile improvement/resource predicates: `Bridge_Able`, `Irrigate_Able`, `Pasturage_Able`, `Mine_Able`, `Fish_Able`, `LongWall_Able`, `Resource_Able`.
- Tile work and feature changes: `Make_New_Work`, `Make_New_Make`, `Clear_Forest_Or_Resource`, `Clear_Mountain`.
- City-on-map helpers: `Reflash_City_Road`, `Make_City_Map`, `Make_City_Wall`, `Make_City_Culvert`, `Del_City_Wall_Or_Culvert`, `Make_City_Train`.
- Named points/place names: `NewLand_Name`, editor tool modes `7/8`.
- Map editor: `Edit_Start`, `Edit_Finish`, `Menu_EditMenu_Init/Quit`, `Put_Sub_EditMenu`, `MLR_NewEdit`, `Read_MLP_Edit`, `MLR_Edit_GameMap`, `Read_MRP_Edit`, `Read_MRR_Edit`.

## City / Economy

- Turn/update: `Do_City`, `Prepare_City_Doing`, `City_Round_Check`.
- Resource/worker calculations: `Cal_City_Resource`, `Cal_City_JobPeople`, `City_Resource_Change`, `UserSet_City_Resource`.
- Growth/mood/economy: `City_People_Born_Rate`, `City_People_Change`, `City_People_Change_Percent`, `City_Happy_Change`, `City_Safe_Change`, `City_Loyal_Change`, `City_Business_Change`, `City_Like_Change`, `City_Business`.
- Building/project logic: `City_Building`, `City_Building_AI`, `City_Build_AI_Build_Able`, `City_Upgrade`, `City_Size_Scale`.
- City UI/events: `City_Manager`, `City_View`, `Event_City_View`, `Put_City_View`, `Put_City_Citizen`, `Put_City_Make`.
- Ownership/capture: `City_Belong_Change`, `City_Capture_Transfer`, `City_Army_Error_Fix`.

## Battle

- Entry points: `Start_Map_Battle_From_Army`, `Start_Map_Battle_From_Tile`.
- Conversion/setup: `Map_To_Battle_Army`, `BattleArmy`, `Prepare_Battle_Tile_Object_Flags`, `Make_Battle_Map`, `Decode_Battle`.
- Arrangement/UI: `Battle_AutoArrange`, `Battle_Arrange_Position`, `Battle_First_Line`, `Battle_Peace_Place`.
- Resolution: `Do_Battle_Army_And_Battle_Die`, `Do_Battle_Stone`, `Diplomat_Battle_Back`, `Diplomat_End_Battle_Back`.

## Diplomacy / Country

- Diplomacy flow: `Diplomat_Start`, `Diplomat_Talking`, `Diplomat_End`, `Diplomat_Running`, `Diplomat_Turn`.
- Actions: `Diplomat_Go_Buy_City`, `Diplomat_Ask_Surrend`, `Diplomat_Steal_Science`, `Diplomat_ScareMonger`, `Diplomat_Crack_Build`, `Diplomat_Commotion`, `Diplomat_AskWhat`, `Diplomat_Ask_Check`.
- Decision helpers: `Diplomat_Answer_Cond_Check`, `Diplomat_Allow`, `Diplomat_Value`, `Diplomat_Compare`.
- Diplomacy UI/order: `Do_Country_Diplomat`, `Load_UI_DIP_EMG`, `Reflash_Dip_City_List`, `Order_Diplomat_*`, `Order_Spy_Choice_Mission`.
- Country state: `CountryPoint_Minus`, `After_Edit_Country`, country/profile editor setup paths.

## Army / Orders / AI

- Order state: `Add_OrderQueue_Army`, `Apply_OrderQueue_Army`, `Order_Check`, `Order_Nothing`, `Order_Go`, `Order_Go_Act`, `Order_Guard`, `Order_Join_*`, `Order_Out_*`, `Order_Forset`.
- Turn jobs/pathing: `Do_Army_TurnJob`, `TestRoad`, `Find_Direct`, `Search_Round`, `Search_Round_Candidate`.
- Ownership/visibility: `Army_Belong_Change`, `Add_New_View`, `Del_Army_View`, `Cancel_All_Army_On_Tile`.
- AI executors: `AI_Army`, `AI_AirPlane`, `AI_AirOilPlane`, `AI_Ship`, `AI_ActShip`, `AI_Carrier`, `AI_Transport`, `AI_Worker`, `AI_Diplomat`, `AI_UnClear`.

## Editor Data Tables

- Unit/building/country/ground/government/science editors live in `Before_Edit_*` setup functions plus matching `After_*/MLP_*` handlers.
- These are semantic oracles for data structures because they bind UI controls directly to table offsets and file names.
- Prioritize them when recovering field names for static definitions.

## Unknown / Triage

- `0x00405b70` `FUN_00405b70`: large, still raw.
- `0x0040da80` `FUN_0040da80`: large, still raw.
- `0x0041bf20` `FUN_0041bf20`: large, near city/resource predicates but not safely named.
- Keep using strings, module callers, and globals read/written before renaming these.

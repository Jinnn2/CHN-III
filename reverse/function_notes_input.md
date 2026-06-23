# Input Function Notes

These notes cover the first Win32 input bridge reached from startup. They are
navigation notes, not final source reconstruction.

## Function `0x0041fd60` - `Main_WindowProc`

## Status

partial, 80%

## Inputs

- `HWND`
- Win32 message id
- `WPARAM`
- `LPARAM`

## Globals Read

- `g_directdraw_ready`
- input/IME globals around `0x00779e20..0x0077c038`
- `DAT_0060afe4` timer/event handle
- `DAT_00707918`, `DAT_00588b94` custom redraw/restore state

## Globals Written

- `g_directdraw_ready`
- `DAT_005dff08` active/capture-ish window state
- keyboard and mouse queues through input bridge helpers

## Calls

- `Input_On_KeyDown`
- `Input_On_KeyUp`
- `Input_On_MouseButtonDown`
- `Input_On_MouseButtonUp`
- `Input_On_MouseMove`
- `Input_Set_MouseCapture`
- `Input_On_InputLangChange_candidate`
- `IME_On_Composition_candidate`
- DirectDraw cleanup/restore helpers
- `DefWindowProcA`

## Observations

- Installed by `Create_Main_Window`.
- Handles lifecycle messages (`WM_CREATE`, `WM_DESTROY`), activation/focus,
  keyboard, mouse, IME, timer, and a custom `0x3b9` message.
- `WM_DESTROY` shuts down platform/display state, shows the cursor, posts quit,
  and logs to `DEBUG.TXT`.
- On activation loss it disables DirectDraw-ready state and releases capture; on
  activation gain it hides the cursor, captures mouse input, and resets input
  state.

## Function `0x005027b0` - `Input_On_KeyDown`

## Status

partial, 80%

## Inputs

- virtual key code

## Globals Read

- key down bitmap around `0x0077b0ac`
- keyboard event ring read/write indices around `0x0077a698`/`0x0077af60`
- modifier/caps state around `0x0077c038`
- key translation tables around `0x005d7aec` and `0x005d7cec`

## Globals Written

- modifier state for Shift/Ctrl/Alt
- key down bitmap
- key event ring entries and event type `1`

## Calls

- `GetKeyState(VK_CAPITAL)`

## Observations

- Queues a key-down event only if the key was not already marked down and the
  64-entry ring has space.
- Uses caps lock and shift state to select one of two key translation tables.

## Function `0x005028b0` - `Input_On_KeyUp`

## Status

partial, 80%

## Observations

- Mirrors `Input_On_KeyDown`; clears modifier/key state and queues event type
  `2` for key release.

## Function `0x00503360` - `Input_On_MouseButtonDown`

## Status

partial, 80%

## Inputs

- button id (`1` left, `2` right from `Main_WindowProc`)
- `LPARAM` x/y

## Globals Written

- current mouse x/y globals around `0x0077ad1c` and `0x0077b1ac`
- mouse event ring entries around `0x0077a194`, `0x0077ac1c`,
  `0x0077b028`, `0x0077af61`

## Observations

- Event type `0` is left down; event type `2` is right down.

## Function `0x005033f0` - `Input_On_MouseButtonUp`

## Status

partial, 80%

## Observations

- Same ring layout as mouse down.
- Event type `1` is left up; event type `3` is right up.

## Function `0x00503480` - `Input_On_MouseMove`

## Status

partial, 75%

## Observations

- Updates current mouse x/y from `LPARAM`.
- When mouse capture is active, clamps to configured bounds and calls
  `SetCursorPos` if the OS cursor moved outside the allowed rectangle.

## Function `0x00503710` - `Input_Set_MouseCapture`

## Status

named, 75%

## Observations

- Writes capture-enabled flag, then calls `SetCapture` or `ReleaseCapture`.

## Function `0x00502c70` - `Input_On_InputLangChange_candidate`

## Status

candidate, 65%

## Observations

- Handles keyboard layout/IME changes.
- Calls `ImmIsIME`, `GetKeyboardLayoutNameA`, registry lookup for layout text,
  and posts message `0x283` with `wParam 0x21`.

## Function `0x00502fd0` - `IME_On_Composition_candidate`

## Status

candidate, 65%

## Observations

- Handles IME composition/result flags.
- Reads several `ImmGetCompositionStringA` buffers. When result text is
  available, feeds committed bytes through the input character helper at
  `0x005029b0`.

## Function `0x00502a00` - `Input_Reset_Keyboard_State`

## Status

partial, 80%

## Inputs

- `HWND` receiving focus.

## Globals Written

- key-down bitmap at `0x0077b0ac`
- keyboard event ring read/write indices around `0x0077af60` and `0x0077a698`

## Calls

- `SetFocus`

## Observations

- Called from the window/input lifecycle when the app needs to regain focus and
  discard stale key state.
- Clears `0x40` dwords starting at the key-state bitmap, then resets the
  keyboard ring indices.

## Function `0x00502a40` - `Input_Is_KeyDownOrModifier`

## Status

partial, 85%

## Inputs

- virtual key code or internal modifier alias.

## Globals Read

- key-down bitmap at `0x0077b0ac`
- modifier bitfield at `0x0077c038`

## Observations

- For `0x82`/`0x83`, returns whether either Shift bit is set.
- For `0x81`/`0xa2`, returns the Ctrl bit.
- For `0x85`/`0xa4`, returns the Alt bit.
- For other values, returns the byte in the key-down bitmap indexed by the low
  byte of the supplied virtual key.

## Function `0x00502b00` - `Input_Pop_KeyEvent_candidate`

## Status

partial, 80%

## Inputs

- pointer to receive a 16-bit translated key/event code.

## Globals Read

- keyboard event ring read/write indices around `0x0077af60` and `0x0077a698`
- key code ring at `0x0077ab9c`
- key event type ring at `0x0077af20`

## Globals Written

- keyboard event ring read index at `0x0077af60`

## Observations

- Returns `0` when the 64-slot ring is empty.
- Otherwise writes the next translated key code to the output pointer, advances
  the read index modulo 64, and returns the queued event type. Current callers
  treat return value `1`/`2` as key down/up style events.
- `App_Frame_Pump`, `Game_Frame_Pump`, modal dialogs, and text-entry paths feed
  its output into `DAT_00748f2e`.

## Function `0x00502b60` - `Input_Release_IME_Resources_candidate`

## Status

candidate, 65%

## Observations

- Releases a COM-like object at `0x0077bfd8`, then frees two input/IME buffers
  at `0x0077c000` and `0x0077c004`.

## Function `0x00502bc0` - `Input_Create_IME_Context_candidate`

## Status

candidate, 70%

## Inputs

- `HWND`

## Calls

- `ImmCreateContext`
- `ImmAssociateContext`

## Observations

- Creates and associates an IME context for the main window, saving the previous
  context.

## Function `0x00502bf0` - `Input_Reassociate_IME_Context_candidate`

## Status

candidate, 70%

## Inputs

- `HWND`

## Calls

- `ImmAssociateContext`

## Observations

- Reassociates the saved IME context when one exists.

## Function `0x004b0c00` - `Read_Keyboard`

## Status

partial, 75%

## Inputs

- No explicit parameters.
- Consumes current key event globals populated by `Input_Pop_KeyEvent_candidate`
  before each frame dispatch.

## Globals Read

- `g_app_screen_state`
- `g_map_interaction_mode`
- `g_editor_mode_enabled`
- `g_request_redraw`
- `g_frame_tick`
- `g_editor_cursor_tile_x`, `g_editor_cursor_tile_y`
- map cursor/view tile globals around `0x0074a348` and `0x0074a350`
- `g_hex_neighbor_delta_x_by_parity`
- `g_hex_neighbor_delta_y_by_parity`
- `g_current_map_scenario_info.horizontal_wrap_setting`
- active army/city globals around `0x007584dc`, `0x00748ff0`, and `0x007584a8`
- current key globals around `0x00748f2e`/`0x00748f2f`

## Globals Written

- `g_input_direction_current`
- `g_input_direction_last`
- input repeat timing globals around `0x00716204` and `0x0071620c`
- map cursor/view tile globals around `0x0074a348` and `0x0074a350`
- map bookmark slot arrays around `0x005c7810`
- `g_editor_mode_enabled`
- `g_request_redraw`
- editor map backup state and land-tile buffer during undo
- active army route/target fields

## Calls

- `Input_Is_KeyDownOrModifier`
- `TestRoad`
- `Tile_Distance_With_Wrap`
- `InRange_NearDest_City_Found`
- `City_Manager`
- `Prepare_City_Doing`
- `Order_Check`
- `Add_OrderQueue_Army`
- `Edit_Start`
- `Edit_Finish`
- `UI_YesNo_Dialog`
- UI window open/close helpers around `0x00472120` and `0x00472320`

## Observations

- Samples Shift/Ctrl/Alt-like state at entry via `Input_Is_KeyDownOrModifier`;
  aliases `0x82`/`0x83`, `0x81`/`0xa2`, and `0x85`/`0xa4` map to the modifier
  bitfield rather than ordinary key bitmap entries.
- Direction keys use the translated chars `H`, `K`, `M`, and `P`. They map to
  hex directions `1`, `7`, `3`, and `5`, then update view/cursor coordinates
  through the parity-indexed hex-neighbor delta tables.
- Direction repeat uses `g_input_direction_last` plus frame/tick thresholds, so
  the function is both key dispatcher and held-key repeater.
- Number keys `1`..`5` implement map bookmarks. With Alt-like state they save
  the current editor/map cursor tile; with Ctrl-like state they clear a slot;
  with no modifier they jump/target a stored slot.
- In map mode, direction and target handling can route active armies through
  `TestRoad`, nearby-city helpers, confirmation dialogs, and order queue
  helpers. This is an input-to-orders bridge, not the final movement formula.
- `C/c` enters the selected city through `City_Manager` and switches map
  interaction state to city mode.
- In editor interaction mode `99`, `Z/z` restores the editor land-tile backup
  when the backup state equals `2`, acting as an undo/rollback path.
- `E/e` toggles `g_editor_mode_enabled`, requests redraw, calls `Edit_Start`
  on entry, and calls `Edit_Finish` on exit. If finishing fails, the function
  restores the editor flag.
- Several Ctrl+Alt chords trigger debug/admin behavior (`D`, `M`, `R`, `T`,
  `V`, `X` families). These remain intentionally under-named until the debug
  globals are mapped.

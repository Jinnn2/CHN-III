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

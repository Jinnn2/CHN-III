# Function Map

This reverse-engineering map is source-like documentation, not recovered original source.
Addresses refer to `China2EX_fontfix8.exe` with image base `0x400000`.

## Render And Display

| Address | Working name | Evidence | Current interpretation |
|---:|---|---|---|
| `0x46d310` | `init_directdraw_runtime()` | Calls `LoadLibrary/GetProcAddress`, `DirectDrawCreate`, `QueryInterface`, `SetCooperativeLevel`, `CreateSurface`. | Initializes DirectDraw, primary surface, and related DirectX components. |
| `0x46d4a3` | `IDirectDraw::SetCooperativeLevel` call site | COM call through `[edx + 0x50]`. | Sets fullscreen/window cooperation. |
| `0x46d4dd` | `IDirectDraw::CreateSurface` call site | COM call through `[edx + 0x18]`. | Creates the primary DirectDraw surface or initial surface group. |
| `0x4f0b1f` | `set_display_mode_from_mode_table()` | Reads `0x58940c`, `0x589410`, `0x58941c`; calls `[edx + 0x54]`. | Sets display mode from the static mode index and width/height tables. |
| `0x4f0f69` | `reset_or_resize_display_mode()` | Reads `0x589418` and `0x589424`; calls `[ecx + 0x54]`; adjusts a window rect. | Resets display mode and host window rectangle around the active logical size. |
| `0x4f0030` | `lock_back_surface()` | Calls surface method `[ecx + 0x64]` on `0x5dff98`. | Locks the CPU-drawn back/logical surface and stores pitch/pointer globals. |
| `0x4f0070` | `unlock_back_surface()` | Calls surface method `[ecx + 0x80]` on `0x5dff98`. | Unlocks the CPU-drawn surface. |
| `0x4f02d0` | `present_dirty_rects()` | Calls `Blt`/`BltFast` from `0x5dff98` to `0x5dff94`. | Main present path from logical/back surface to primary/front surface. |
| `0x4f0ce0` | `create_front_surface()` | `CreateSurface` into `0x5dff94`; caps `0x4200`. | Creates primary/front surface. |
| `0x4f0de0` | `create_back_surface()` | `CreateSurface` into `0x5dff98`; width/height from mode table. | Creates CPU-drawn back/logical surface at current mode size. |
| `0x4f81e0` | `init_surface_pixel_state()` | Calls surface method `[eax + 0x58]` and `[edx + 0x54]`; writes globals around `0x771b90` and `0x5cffxx`. | Reads surface description and pixel format, then initializes pitch/buffer conversion state. |
| `0x4c2da0` | `apply_resolution_mode(index, skip_redraw)` | Writes `0x734c08/0x734c14`, `0x734c10/0x734c0c`; clamps windows. | Applies logical/client size from the mode table. |
| `0x478eb0` | `main_menu_init()` | Loads `MAINMENU`, `MENU_ITEM.EMG`, `MAINMENU.XMG`; calls `0x48b4f0(0x200, 0x180)`. | Initializes main menu resources and a hard-coded 1024x768 center/viewport baseline. |
| `0x49bec0` | `load_tmg_background(name, copy_header)` | Opens `GRAPH\\<name>.TMG`, reads PCX-like header, stores width/height in `0x7150e0/0x715058`. | Loads static `.TMG` backgrounds such as `MAINMENU.TMG`. |
| `0x48b752` | `mark_dirty_rect_x()` | Writes `0x57d080`. | Dirty rect left/x state for present. |
| `0x48b75a` | `mark_dirty_rect_y()` | Writes `0x57d084`. | Dirty rect top/y state for present. |

## Resolution State

| Address | Type | Value in original | Meaning |
|---:|---|---:|---|
| `0x58940c` | `uint32` | `1` | Startup display mode index. |
| `0x589410` | `uint32[3]` | `800, 1024, 1280` | Width table. |
| `0x58941c` | `uint32[3]` | `600, 768, 1024` | Height table. |
| `0x75cf80` | `uint32` | runtime | Active/right/buffer width-like value after `SetDisplayMode`. |
| `0x75cf84` | `uint32` | runtime | Active/bottom/buffer height-like value after `SetDisplayMode`. |
| `0x734c08` | `uint32` | runtime | Window/client width-like value used during display reset. |
| `0x734c14` | `uint32` | runtime | Window/client height-like value used during display reset. |
| `0x734c10` | `uint32` | runtime | Horizontal center offset from 800-wide baseline: `(width - 800) / 2`. |
| `0x734c0c` | `uint32` | runtime | Vertical center offset from 600-high baseline: `(height - 600) / 2`. |
| `0x57d080` | `uint32` | runtime | Dirty rect x/left coordinate candidate. |
| `0x57d084` | `uint32` | runtime | Dirty rect y/top coordinate candidate. |
| `0x77b1b4` | `uint32` | runtime | View/cursor center x-like value; main menu init hard-codes `0x200`. |
| `0x77b1c8` | `uint32` | runtime | View/cursor center y-like value; main menu init hard-codes `0x180`. |
| `0x5dff94` | `surface*` | runtime | Primary/front surface used as blit destination. |
| `0x5dff98` | `surface*` | runtime | Back/logical surface used as blit source and CPU lock target. |

## Resource And UI Names From Strings

These strings are useful anchors for future cross-reference work.

| String | Likely subsystem |
|---|---|
| `UI.EMG`, `NEWUI.EMG`, `MOUSE.EMG`, `METAL.EMG` | Core UI and cursor graphics. |
| `MAINMENU.EMG`, `MAINMENU.XMG` | Main menu UI overlay/sprite content. |
| `UI_BATTLE.EMG`, `UI_CITY.EMG`, `UI_DIP.EMG` | In-game UI panels. |
| `MENU_ITEM.EMG`, `UI_String.EMG`, `UI_STRING.XMG` | Menu items and UI text sprites. |
| `GRAPH\\MAINMENU.TMG`, inferred through resources | Static 1024x768 background layer. |

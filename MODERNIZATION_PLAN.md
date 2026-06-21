# CHN-III Resolution and UI Modernization Plan

## Current State

- The playable executable path is `China2EX_fontfix8.exe`.
- Display compatibility is handled by `dgVoodoo.conf` plus `ModernLauncher.ps1`.
- The launcher currently supports three output modes: keep 4:3 fullscreen, stretched fullscreen, and windowed.
- The directly editable UI background set is under `GRAPH` and uses PCX-like 24-bit files with `.TMG` or `.pcx` extensions.
- The editable working folder is `ModernUIExport`.
- `ModernUIExport` has been restored from `_archive/cleanup-20260622/ui-artifacts/ModernUIExport`.
- The high-resolution `MAINMENU.png` and `LOADING.png` drafts have been converted to importable 1024x768 24-bit BMP files.

## Resource Workspaces

- `ModernUIExport/GRAPH`: importable 24-bit BMP files at the exact game resource size.
- `ModernUIExport/NEW`: higher-resolution source drafts. Current known sources are 1448x1086 PNG files for the main menu and loading screen.
- `_archive/cleanup-20260622/ui-artifacts`: historical extracted resources and probes kept as backup evidence.

## Tooling

- Export current game UI backgrounds:
  `python tools\ui_probe\export_graph_ui.py`
- Validate editable BMP files before import:
  `python tools\ui_probe\validate_graph_ui.py`
- Convert high-resolution `NEW` PNG drafts into importable BMP files:
  `python tools\ui_probe\prepare_new_ui_sources.py`
- Import edited BMP files back into game resources:
  `python tools\ui_probe\import_graph_ui.py`
- Probe executable DirectDraw resolution metadata:
  `python tools\reverse_probe\render_probe.py`
- Generate the 1280x1024 internal-resolution test executable:
  `python tools\reverse_probe\patch_resolution_mode.py --force --mode-index 2`

## Confirmed Editable GRAPH Files

- `back.TMG`: 1024x768
- `CAST.TMG`: 1024x768
- `DRAGON.TMG`: 1024x768
- `Loading.TMG`: 1024x768
- `MAINMENU.TMG`: 1024x768
- `MEET_EAST.TMG`: 1024x768
- `MEET_MODEM.TMG`: 1024x768
- `MEET_OLD.TMG`: 1024x768
- `MEET_WEST.TMG`: 1024x768
- `SCORELIST.TMG`: 1024x768
- `USER_35.pcx`: 640x480
- `USER_81.pcx`: 640x480

## Recommended Resolution Strategy

There are two separate targets:

- Compatibility scaling: use `dgVoodoo` to make the existing 1024x768 game look correct on modern displays.
- New-version rendering: change the executable's internal DirectDraw mode and then repair UI, mouse, and game layout logic.

The second target is possible to investigate because the executable contains an internal resolution mode table, but it should be treated as a staged reverse-engineering effort rather than a pure asset replacement.

1. Keep the game in 4:3 logical layout.
2. Use `Keep4x3` as the recommended mode for modern monitors.
3. Use `Fill` only as an optional stretched mode.
4. Keep `Windowed` for debugging, resource verification, and capture.
5. Avoid claiming native widescreen until executable-level coordinate and layout behavior is understood.

## Render Logic Findings

- `China2EX_fontfix8.exe` imports `DDRAW.dll!DirectDrawCreateEx`.
- The executable uses DirectDraw COM vtable calls, so most render calls do not appear by function name in the import table.
- DirectDraw initialization has been located around `0x46d330` to `0x46d665`.
- `0x46d4a3` calls `IDirectDraw::SetCooperativeLevel`.
- `0x46d4dd` calls `IDirectDraw::CreateSurface`.
- `0x4f0b1f` calls `IDirectDraw::SetDisplayMode` using an internal mode table.
- `0x4f0f69` also calls `IDirectDraw::SetDisplayMode` using global width/height values.
- Static mode index and table:
  - `0x58940c`: current mode index, currently `1`.
  - `0x589410`: width table: `800, 1024, 1280`.
  - `0x58941c`: height table: `600, 768, 1024`.
- This means the game already knows about at least three internal fullscreen modes, with 1024x768 selected by default.
- `China2EX.exe` and `China2EX_fontfix8.exe` differ by only 26 bytes near font-related strings, so the fontfix build is not a separate render rewrite.

Run this probe to re-check the render findings:

`python tools\reverse_probe\render_probe.py`

## New-Version Development Strategy

1. Build a controlled binary-patch experiment that changes only the startup mode index from `1` to `2`, selecting the existing 1280x1024 internal mode. This is now implemented by `tools\reverse_probe\patch_resolution_mode.py`.
2. Launch in windowed or fake-fullscreen mode and capture whether menus, mouse hit zones, cutscenes, and map rendering still work. Use `start_modtest_1280.bat` for the 1280x1024 test build.
3. If 1280x1024 works, patch or redirect the mode table to a 4:3 modern target such as 1440x1080 or 1600x1200. This is now staged as `start_modtest_1600x1200.bat`.
4. Only after 4:3 internal high resolution is stable, test 16:9 targets such as 1280x720 or 1600x900.
5. Expect 16:9 to require UI coordinate repair, mouse coordinate mapping, and asset/layout changes.
6. Keep an external wrapper path available as the compatibility fallback while the executable path evolves.

## Recommended UI Strategy

1. Phase 1: Replace only `MAINMENU` and `Loading` using the existing high-resolution source drafts. These two converted BMP files already pass validation.
2. Phase 2: Refresh static 1024x768 background screens: `back`, `DRAGON`, `CAST`, meeting backgrounds, and score list.
3. Phase 3: Investigate `.EMG`, `.XMG`, `.IMG`, and `.IDI` formats for in-game panels, buttons, icons, and sprites.
4. Phase 4: Only after format coverage is known, decide whether to modernize in-game HUD and dialog components.

## Proposed First Test

Resolution logic test:

1. Run `start_modtest_1280.bat`.
2. Confirm the game opens through `China2EX_modtest.exe`.
3. Check whether the main menu fills or clips at 1280x1024.
4. Check whether mouse hit boxes align with visible menu items.
5. Start or load a game and check map rendering, scrolling, dialogs, and ending the turn.
6. If the game fails to start, inspect `DEBUG.TXT`, `TRACE.TXT`, `Error.txt`, and any `dgVoodoo` log.

Current status:

- `China2EX_modtest.exe` is generated by `patch_resolution_mode.py`.
- `render_probe.py China2EX_modtest.exe` confirms mode index `2`.
- A local launch smoke test started `China2EX_modtest.exe` without immediate crash.
- Manual verification for 1280x1024 passed.
- The next test build is `China2EX_modtest_1600x1200.exe`, generated by `start_modtest_1600x1200.bat`.
- Static verification and launch smoke test for 1600x1200 passed; manual verification is tracked in `MODTEST_1600x1200_CHECKLIST.md`.
- Reverse docs now track the display mode, surface present path, and logical-size globals under `reverse/`.
- `0x4c2da0` applies mode-table width/height to `0x734c08/0x734c14` and computes offsets from an 800x600 baseline, so the engine has partial large-canvas support even when some UI resources remain fixed-size.
- `0x478eb0` is now identified as the main menu initializer. It loads `MAINMENU`, `MENU_ITEM.EMG`, and `MAINMENU.XMG`, but also hard-codes a `512,384` center/viewport baseline, matching 1024x768.
- `0x49bec0` loads static `.TMG` backgrounds and derives dimensions from the file header. Current `MAINMENU.TMG` is still 1024x768, so a larger DirectDraw surface can exist while the background content remains 1024x768.
- `China2EX_modtest_1600x1200_menuviewport.exe` is a targeted experiment: it patches mode 2 to 1600x1200 and patches the main-menu center constants from `512,384` to `800,600`. Launch it through `start_modtest_1600x1200_menuviewport.bat`.
- The first `menuviewport` manual attempt opened the launcher menu because the batch file passed unsupported arguments. The batch file has been corrected; retest is needed before drawing conclusions.
- `0x4f5ce9` is the common image blit routine used by main menu display paths. It reads `uint16 width` and `uint16 height` from the image payload and clips against the active draw bounds, so it does not appear to hard-code 1024x768 by itself.

Static UI import test:

1. Run `python tools\ui_probe\validate_graph_ui.py`.
2. Run `python tools\ui_probe\import_graph_ui.py`.
3. Launch with `start_fixed.bat` or `ModernLauncher.bat`.
4. Verify the main menu and loading screen appear correctly.
5. If the result is good, keep `ModernUIBackup` as rollback evidence and proceed to the next static screens.

## Design Direction

Use a restrained strategy-game modernization style:

- Preserve the original 4:3 composition and interaction hit zones.
- Improve contrast, legibility, and background polish.
- Avoid tiny decorative text that will blur after downsampling.
- Avoid changing button positions unless the executable hit boxes are patched or verified.
- Prefer historically grounded military/diplomacy visual language over generic neon or web-dashboard styling.

## Open Technical Questions

- Whether mode index `2` / 1280x1024 is fully functional or only partially implemented.
- Whether the mode table can be patched to arbitrary 4:3 and 16:9 sizes without breaking surface allocation.
- Whether mouse hit boxes and UI coordinates are tied to 1024x768, mode-scaled, or resource-driven.
- Whether `.EMG` files contain UI panels/buttons in a format that can be round-tripped.
- Whether `.XMG`, `.IMG`, and `.IDI` contain palette-indexed sprites, compressed sheets, or metadata tables.
- Whether menu button hit boxes are hard-coded or resource-driven.

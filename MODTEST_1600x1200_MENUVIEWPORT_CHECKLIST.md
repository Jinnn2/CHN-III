# 1600x1200 Main Menu Viewport Experiment Checklist

Test executable:

`China2EX_modtest_1600x1200_menuviewport.exe`

Launch command:

`start_modtest_1600x1200_menuviewport.bat`

## Static Verification

- [x] `patch_mainmenu_viewport.py` generates `China2EX_modtest_1600x1200_menuviewport.exe`.
- [x] `render_probe.py China2EX_modtest_1600x1200_menuviewport.exe` reports mode index `2`.
- [x] Mode 2 reports `1600x1200`.
- [x] Main-menu constants at `0x478ee6/0x478eeb/0x478f1b/0x478f25` are patched to `600/800/800/600`.

## Manual Comparison

- [ ] The executable starts without immediate crash.
- [ ] Main menu background is visible.
- [ ] Visible UI/background region differs from `China2EX_modtest_1600x1200.exe`.
- [ ] Main menu still appears as a 1024x768 block inside the larger window.
- [ ] Mouse cursor appears.
- [ ] Menu hit boxes align with visible buttons.
- [ ] Start/new-game flow can be entered.

## Interpretation

- If the visible menu region changes, the hard-coded main-menu viewport center is part of the 1024x768 lock and should be promoted to resolution-derived state.
- If nothing changes, the primary remaining cap is likely the `MAINMENU.TMG` source size or the `.TMG` draw routine rather than this center/viewport state.
- If hit boxes change but visuals do not, input/layout and background painting are separate upgrade tracks.

Current status:

- Static patch verification passed.
- The first manual attempt opened the launcher menu because the batch file passed unsupported launcher arguments.
- That attempt likely launched `China2EX_modtest_1600x1200.exe`, not `China2EX_modtest_1600x1200_menuviewport.exe`, so the visual comparison is not valid yet.
- The batch file has been corrected to pass `-LaunchMode Windowed -GameExeName China2EX_modtest_1600x1200_menuviewport.exe`.

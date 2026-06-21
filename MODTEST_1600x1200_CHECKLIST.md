# 1600x1200 Internal Resolution Test Checklist

Test executable:

`China2EX_modtest_1600x1200.exe`

Launch command:

`start_modtest_1600x1200.bat`

## Static Verification

- [x] `patch_resolution_mode.py` generates `China2EX_modtest_1600x1200.exe`.
- [x] `render_probe.py China2EX_modtest_1600x1200.exe` reports mode index `2`.
- [x] Mode 2 reports `1600x1200`.
- [x] The executable starts without immediate crash.
- [ ] Confirm the rendered window is actually using the 1600x1200 internal mode.

## Menu Verification

- [ ] Main menu background is visible.
- [ ] Main menu is not clipped, black-bordered incorrectly, or stretched unexpectedly.
- [ ] Mouse cursor appears.
- [ ] Menu hit boxes align with visible buttons.
- [ ] Start/new-game flow can be entered.
- [ ] Load-game flow can be entered.

## Gameplay Verification

- [ ] Map renders correctly.
- [ ] Map scroll works in all directions.
- [ ] Top/bottom/side UI panels render correctly.
- [ ] Dialog windows render correctly.
- [ ] Mouse hit boxes align inside dialogs.
- [ ] Turn progression works.
- [ ] Save and load work.

## Interpretation

- If this passes, the executable's mode table can likely be extended to arbitrary 4:3 modes.
- If this fails while 1280x1024 passes, the next step is to locate allocation limits or DirectDraw enumeration constraints.

Current status:

- Static patch verification passed.
- Local launch smoke test passed; visual/menu/gameplay behavior still needs manual verification.

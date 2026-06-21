# 1280x1024 Internal Resolution Test Checklist

Test executable:

`China2EX_modtest.exe`

Launch command:

`start_modtest_1280.bat`

## Static Verification

- [x] `patch_resolution_mode.py` generates `China2EX_modtest.exe`.
- [x] `render_probe.py China2EX_modtest.exe` reports mode index `2`.
- [x] `China2EX_modtest.exe` starts without immediate crash.
- [x] Confirm the rendered window is actually using the 1280x1024 internal mode.

## Menu Verification

- [x] Main menu background is visible.
- [x] Main menu is not clipped, black-bordered incorrectly, or stretched unexpectedly.
- [x] Mouse cursor appears.
- [x] Menu hit boxes align with visible buttons.
- [x] Start/new-game flow can be entered.
- [x] Load-game flow can be entered.

## Gameplay Verification

- [x] Map renders correctly.
- [x] Map scroll works in all directions.
- [x] Top/bottom/side UI panels render correctly.
- [x] Dialog windows render correctly.
- [x] Mouse hit boxes align inside dialogs.
- [x] Turn progression works.
- [x] Save and load work.

Result:

- Manual verification passed. User reported everything works normally.

## Failure Evidence

If a test fails, capture:

- Screenshot or short screen recording.
- `DEBUG.TXT`
- `TRACE.TXT`
- `Error.txt`
- Any `dgVoodoo` log created in the game folder.
- Whether the same step works in the original `China2EX_fontfix8.exe`.

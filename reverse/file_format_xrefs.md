# File Format Xrefs

This file tracks executable references to game file formats and resource
containers. It is a navigation index, not a complete unpacking spec.

## DAT

Functions:

- `0x00473270` `Load_Dat`: main DAT/save/scenario loader. Strings mention map,
  city, army, memory buffer, decompression, and minimap decode.
- `0x00477ff0` `Load_EMG_Base`: loads or regenerates cache tables:
  `C_TABLE.DAT`, `F_TABLE.DAT`, `D_TABLE.DAT`.
- `0x004c60a0` `ShutDown_Game`: writes `CONFIG.DAT` and `KEYDEF.DAT`.
- `0x00452110` `Before_Edit_Army`: checks/backs up `ARMYBASE.DAT`.
- `0x00454570` `Before_Edit_Build`: checks/backs up `BUILD.DAT`.
- `0x004578a0` `Before_Edit_Empire_Country`: reads/writes `EMPIRE.DAT` or
  `EMPIRE_%d.USR`.
- `0x0045d6f0` `Before_Edit_Goverment`: checks/backs up `GOVERMENT.DAT`.
- `0x0045e4d0` `Before_Edit_Ground`: checks/backs up `GROUND.DAT`.
- `0x0045ee10` `Before_Edit_Empire_Hero`: reads/writes `HERO.DAT` or
  `HERO_%d.USR`.

Files observed:

- `CONFIG.DAT`
- `KEYDEF.DAT`
- `C_TABLE.DAT`
- `F_TABLE.DAT`
- `D_TABLE.DAT`
- `ARMYBASE.DAT`
- `BUILD.DAT`
- `EMPIRE.DAT`
- `GOVERMENT.DAT`
- `GROUND.DAT`
- `HERO.DAT`
- `SCORE.DAT`

Notes:

- `Load_Dat` is the key File IO entry point and should get function notes
  before deeper formula work.
- Editor setup functions are the best route for static DAT table field names.

## EMG

Functions:

- `0x004789e0` `Load_EMG_Resource`: safe EMG loader wrapper.
- `0x00478b30` `Free_EMG_Resource`: safe EMG free wrapper.
- `0x00477ff0` `Load_EMG_Base`: loads base runtime EMG banks.
- `0x0046b850` `Load_UI_String_EMG`: loads `UI_STRING.EMG`.
- `0x0046cc70` `Load_UI_String_EMG_XMG`: loads `UI_STRING.EMG`.
- `0x0047e230` `Load_MAINMENU_EMG`: loads `MAINMENU.EMG`.
- `0x004ec1a0` `Load_UI_DIP_EMG`: loads `UI_DIP.EMG`.
- `0x00419f30` `Battle_Arrange_Position`: loads `UI_BATTLE.EMG`.
- `0x00425940` `City_Manager`: loads `UI_CITY.EMG`.
- `0x004891a0` `UI_YesNo_Dialog` family: loads `UI_YN.EMG`.
- `0x0046e950` `Init_SetUp`: loads `METAL.EMG`, `NEWUI.EMG`, `MOUSE.EMG`,
  `UI.EMG`.

Files observed:

- `DEC.EMG`
- `NEW_GROUND.EMG`
- `UNCLEAR.EMG`
- `MAKE.EMG`
- `BUILD.EMG`
- `BUILD_SPEC.EMG`
- `CITY.EMG`
- `NPC1.EMG`, `NPC2.EMG`, `NPC3.EMG`
- `ROAD.EMG`
- `FADE.EMG`
- `GON_ACT.EMG`
- `RESOURCE.EMG`
- `STONE.EMG`
- `METAL.EMG`
- `NEWUI.EMG`
- `MOUSE.EMG`
- `UI.EMG`
- `UI_STRING.EMG`
- `UI_CITY.EMG`
- `UI_DIP.EMG`
- `UI_BATTLE.EMG`
- `UI_YN.EMG`
- `MAINMENU.EMG`
- `MENU_ITEM.EMG`
- `BATTLE_GRD.EMG`

Used by:

- UI rendering and menu panels.
- Battle UI and battle ground resources.
- City/diplomacy screens.
- Map sprite resources and fade/color table generation.

## XMG

Functions:

- `0x00478ac0` `Load_XMG_Resource`: safe XMG loader wrapper.
- `0x00478b90` `Free_XMG_Resource`: safe XMG free wrapper.
- `0x00477ff0` `Load_EMG_Base`: loads base runtime XMG banks.
- `0x0046cc70` `Load_UI_String_EMG_XMG`: loads `UI_STRING.XMG`.
- `0x00478eb0` `MainMenu_Init`: loads `MAINMENU.XMG`.

Files observed:

- `SHELL.XMG`
- `BUILD.XMG`
- `UNCLEAR.XMG`
- `EXPLODE.XMG`
- `UNCLEAR_EXP.XMG`
- `EVENT.XMG`
- `DISEASE.XMG`
- `STONE.XMG`
- `UI_STRING.XMG`
- `MAINMENU.XMG`

Used by:

- Sprite/frame banks paired with EMG UI/resource groups.
- Main menu and UI string rendering.

## IMG / IDI

Functions:

- `0x00478a50` `Safe_LoadIMG`: image-bank load wrapper.
- `0x00478b60` `Safe_FreeIMG`: image-bank free wrapper.
- `0x00478dc0` `CloseIndexIMG`: closes indexed IMG resources.
- `0x00477ff0` `Load_EMG_Base`: loads `FLAG.IMG`.
- `0x0045d0d0` `Save_IMG_Flag`: writes `FLAG.IMG` from 100 flag blocks.
- Country/profile editor and `Load_Dat`: format `DIP_%02d.IMG` / `.IDI`.

Files observed:

- `FLAG.IMG`
- `DIP_%02d.IMG`
- `DIP_%02d.IDI`

Used by:

- Empire/country flags.
- Country portraits and preview handles.

## TMG

Functions:

- `0x0049bec0` `Load_TMG_Background`: reads `GRAPH\<name>.TMG`.
- `0x00478eb0` `MainMenu_Init`: loads `MAINMENU.TMG`.
- `0x004ec1a0` `Load_UI_DIP_EMG`: loads diplomacy background.
- `0x0046b850` / `0x0046cc70`: load `SCORELIST` background.
- `0x0047ee50` `Menu_EditMenu_Init`: loads `DRAGON` background.
- `0x0046e950` `Init_SetUp`: loads `Loading` background.

Files observed:

- `GRAPH\MAINMENU.TMG`
- `GRAPH\SCORELIST.TMG`
- `GRAPH\DRAGON.TMG`
- `GRAPH\Loading.TMG`
- Diplomacy backgrounds formed dynamically in `Load_UI_DIP_EMG`.

Used by:

- Static full-screen backgrounds.
- Main menu, editor menu, score/history, loading, diplomacy screens.

## PCX

Functions:

- `0x0049bec0` `Load_TMG_Background`: reads a PCX-like header inside TMG.
- `0x0045c330` `MouseOn_Edit_Sel_Pcx_File`: editor PCX file-selection UI.

Used by:

- TMG decoding/header handling.
- Map/editor image selection.

## AVI

Functions:

- Not yet mapped in the current status board.

Next action:

- Search string/xref inventory for AVI names before assigning a loader.

## SAV / Save

Functions:

- `0x00473270` `Load_Dat`: contains save decompression/memory-buffer strings and
  reconstructs scenario state.
- Main save/write counterpart is not yet isolated in the current status board.

Files observed:

- `SAVE.DAT` runtime file in worktree.
- `Save/SAVE00/` runtime directory in worktree.
- `SCORE.DAT` score/history runtime file.

Notes:

- Runtime save/config files should not be committed with reverse-engineering
  docs.
- SaveGame container struct is still a candidate in `data_structures.md`.

# China2EX Rebuild Workbench

This directory is the first compiled rebuild skeleton for the reverse-engineering effort.

It is not a gameplay rebuild yet. The goal of this stage is narrower:

- turn the recovered boot path into a real buildable Win32 program
- create a stable place to replace placeholders with recovered behavior
- keep the mapping to `reverse/ghidra_export` explicit

## Current Status

The executable builds with MinGW `gcc` via:

```bat
build.bat
```

Current output:

- `build\china2ex_rebuild.exe`

What it already reconstructs:

- a Win32 `WinMain` entry point
- single-instance mutex behavior
- command-line flag parsing for `DEMO`, `LOAD`, and `EDIT`
- startup sequencing aligned to the recovered path:
  `WinMain -> Process_CommandLine_Args -> Init_SetUp -> frame pump`
- a placeholder main-menu state and a placeholder game-loop state

## Reverse Mapping

The current code maps directly to these recovered functions:

- `App_WinMain_Entry`:
  [app_winmain_entry.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/game/app_winmain_entry.c:1)
- `Process_CommandLine_Args`:
  [process_command_line_args.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/game/process_command_line_args.c:1)
- `Init_SetUp`:
  [init_setup.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/game/init_setup.c:1)
- `MainMenu_Init`:
  [main_menu_init.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/ui/main_menu_init.c:1)
- `App_Frame_Pump`:
  [app_frame_pump.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/game/app_frame_pump.c:1)
- `Game_Frame_Pump`:
  [game_frame_pump.c](/c:/baidunetdiskdownload/zhongguo2lianhe/zhongguo2lianhe/reverse/ghidra_export/game/game_frame_pump.c:1)

## Best Next Steps

The highest-value next steps are:

1. add a small runtime layer for logging, timing, and global state names from the recovered notes
2. replace the placeholder main-menu draw path with decoded `MAINMENU.TMG` loading
3. formalize a resource abstraction for `.EMG`, `.XMG`, and `.TMG`
4. decide whether we keep a Win32/GDI stepping stone or jump straight to SDL2 for rendering portability

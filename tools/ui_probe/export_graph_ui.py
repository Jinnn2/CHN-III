#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "ModernUIExport" / "GRAPH"
GAME_DIR = ROOT / "GRAPH"
TOOL = ROOT / "tools" / "ui_probe" / "pcx_tmg_tool.py"

FILES = [
    "back.TMG",
    "CAST.TMG",
    "DRAGON.TMG",
    "Loading.TMG",
    "MAINMENU.TMG",
    "MEET_EAST.TMG",
    "MEET_MODEM.TMG",
    "MEET_OLD.TMG",
    "MEET_WEST.TMG",
    "SCORELIST.TMG",
    "USER_35.pcx",
    "USER_81.pcx",
]


README = """Editable UI background exports for China2.

Edit these BMP files, then run this from the game folder:

python tools\\ui_probe\\validate_graph_ui.py
python tools\\ui_probe\\import_graph_ui.py

Important:
- Keep each image at its original size.
- Keep BMP as 24-bit RGB.
- Do not rename files.
- The importer creates backups in ModernUIBackup before replacing game files.

File map:
- back.bmp -> GRAPH\\back.TMG, 1024x768
- CAST.bmp -> GRAPH\\CAST.TMG, 1024x768
- DRAGON.bmp -> GRAPH\\DRAGON.TMG, 1024x768
- Loading.bmp -> GRAPH\\Loading.TMG, 1024x768
- MAINMENU.bmp -> GRAPH\\MAINMENU.TMG, 1024x768
- MEET_EAST.bmp -> GRAPH\\MEET_EAST.TMG, 1024x768
- MEET_MODEM.bmp -> GRAPH\\MEET_MODEM.TMG, 1024x768
- MEET_OLD.bmp -> GRAPH\\MEET_OLD.TMG, 1024x768
- MEET_WEST.bmp -> GRAPH\\MEET_WEST.TMG, 1024x768
- SCORELIST.bmp -> GRAPH\\SCORELIST.TMG, 1024x768
- USER_35.bmp -> GRAPH\\USER_35.pcx, 640x480
- USER_81.bmp -> GRAPH\\USER_81.pcx, 640x480
"""


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    exported = 0
    for name in FILES:
        original = GAME_DIR / name
        if not original.exists():
            print(f"skip missing game resource: {original}")
            continue

        bmp = EXPORT_DIR / (Path(name).stem + ".bmp")
        subprocess.check_call([sys.executable, str(TOOL), "export", str(original), str(bmp)])
        exported += 1

    (EXPORT_DIR / "README.txt").write_text(README, encoding="utf-8")
    print(f"done. exported {exported} file(s) to {EXPORT_DIR}")


if __name__ == "__main__":
    main()

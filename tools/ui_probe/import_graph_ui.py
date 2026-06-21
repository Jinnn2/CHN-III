#!/usr/bin/env python3
import shutil
import subprocess
import sys
from datetime import datetime
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


def main():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "ModernUIBackup" / f"GRAPH_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    changed = 0
    for name in FILES:
        original = GAME_DIR / name
        bmp = EXPORT_DIR / (Path(name).stem + ".bmp")
        if not bmp.exists():
            print(f"skip missing edited image: {bmp}")
            continue

        shutil.copy2(original, backup_dir / name)
        tmp = backup_dir / name
        subprocess.check_call([sys.executable, str(TOOL), "import", str(original), str(bmp), str(tmp)])
        shutil.copy2(tmp, original)
        changed += 1
        print(f"updated {original}")

    print(f"done. updated {changed} file(s). backup: {backup_dir}")


if __name__ == "__main__":
    main()

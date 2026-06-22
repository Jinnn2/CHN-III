#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(args):
    print("+", " ".join(str(arg) for arg in args))
    subprocess.check_call([sys.executable, *map(str, args)], cwd=ROOT)


def main():
    run([
        ROOT / "tools" / "ui_probe" / "prepare_highres_graph.py",
        "--width",
        "1280",
        "--height",
        "1024",
        "--install",
    ])
    run([
        ROOT / "tools" / "reverse_probe" / "patch_startup_mode.py",
        "--force",
        "--width",
        "1280",
        "--height",
        "1024",
        "--output",
        ROOT / "China2EX_mod_1280x1024.exe",
    ])
    print("ready: China2EX_mod_1280x1024.exe")


if __name__ == "__main__":
    main()

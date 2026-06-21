@echo off
cd /d "%~dp0"
python tools\reverse_probe\patch_resolution_mode.py --force --mode-index 2 --mode-width 1600 --mode-height 1200 --output China2EX_modtest_1600x1200.exe
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName China2EX_modtest_1600x1200.exe

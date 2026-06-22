@echo off
cd /d "%~dp0"
python tools\reverse_probe\patch_startup_mode.py --force --width 1280 --height 1024 --output China2EX_modtest_startmode2_1280x1024.exe
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName "China2EX_modtest_startmode2_1280x1024.exe"

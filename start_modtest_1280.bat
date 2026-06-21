@echo off
cd /d "%~dp0"
python tools\reverse_probe\patch_resolution_mode.py --force --mode-index 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName China2EX_modtest.exe

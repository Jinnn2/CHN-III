@echo off
cd /d "%~dp0"
python tools\reverse_probe\patch_1280x1024_mod.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName "China2EX_mod_1280x1024.exe"

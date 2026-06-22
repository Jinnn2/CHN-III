@echo off
cd /d "%~dp0"
python tools\reverse_probe\patch_mainmenu_viewport.py --force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName "China2EX_modtest_1600x1200_menuviewport.exe"

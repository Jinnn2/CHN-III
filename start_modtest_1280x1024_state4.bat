@echo off
setlocal
cd /d "%~dp0"
C:\Python314\python.exe tools\reverse_probe\patch_startup_mode.py --force --width 1280 --height 1024 --initial-screen-state 4 --output China2EX_modtest_1280x1024_state4.exe
start "" "%cd%\China2EX_modtest_1280x1024_state4.exe"

@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Windowed -GameExeName "China2EX_modtest_1600x1200_menuviewport.exe"

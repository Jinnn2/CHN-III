@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ModernLauncher.ps1" -LaunchMode Keep4x3

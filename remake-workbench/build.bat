@echo off
setlocal

where gcc >nul 2>nul
if errorlevel 1 (
    echo gcc was not found on PATH.
    exit /b 1
)

if not exist build mkdir build

gcc ^
    -std=c11 ^
    -Wall -Wextra ^
    -Isrc ^
    src\main.c src\app.c src\resources.c ^
    -lgdi32 -luser32 ^
    -o build\china2ex_rebuild.exe

exit /b %errorlevel%

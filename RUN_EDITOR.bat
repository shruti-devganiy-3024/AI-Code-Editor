@echo off
cd /d "%~dp0"

if exist "dist\AICodeEditor.exe" (
    start "" "dist\AICodeEditor.exe"
) else (
    echo ERROR: EXE not found!
    echo Please run BUILD_EXE.bat first.
    pause
)
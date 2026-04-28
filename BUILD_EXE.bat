@echo off
cd /d "%~dp0"

title AI Code Editor v2.0 - EXE Builder

echo.
echo ========================================
echo   AI Code Editor v2.0 - EXE Builder
echo ========================================
echo.

:: Step 1: Check Python
echo [1/4] Checking Python...
py --version
if %ERRORLEVEL% NEQ 0 (
    echo Python not found!
    pause
    exit /b
)

:: Step 2: Check PyInstaller
echo [2/4] Checking PyInstaller...
py -m PyInstaller --version
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    py -m pip install pyinstaller
)

:: Step 3: Clean old build
echo [3/4] Cleaning old files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AICodeEditor.spec del AICodeEditor.spec

:: Step 4: Build EXE
echo [4/4] Building EXE...
py -m PyInstaller ^
--onefile ^
--windowed ^
--name AICodeEditor ^
--add-data "chats;chats" ^
--add-data "code;code" ^
--add-data "data;data" ^
--add-data "headers;headers" ^
AI_Code_Editor_Offline_v2_0.py

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo ========================================
echo.

pause
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 3DTRF Builder
color 0E

echo.
echo  =======================================================
echo     3DTRF Build Script
echo     Packaging application into Standalone EXE
echo  =======================================================
echo.

:: Check for PyInstaller/Flet
echo [INFO] Verifying packaging tools...
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not found. Installing...
    python -m pip install pyinstaller
)
python -m pip show flet >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Flet not found in host python. Installing...
    python -m pip install flet
)

echo [INFO] Starting Flet Pack process...
echo [INFO] This will include the portable engine in 'deps'...
echo.

:: Run flet pack -> Using standard PyInstaller since 'flet pack' is deprecated in newer versions
:: --name: Output filename
:: --add-data: Include the deps folder. Format is "source;destination"
:: --noconsole: If you want a windowed app without a CMD window
pyinstaller --noconfirm --name 3DTRF --noconsole --add-data "%~dp0deps;deps" --add-data "%~dp0requirements.txt;." --add-data "%~dp0convert.py;." "%~dp0app.py"

if %errorlevel% equ 0 (
    echo.
    echo  =======================================================
    echo  [SUCCESS] Build Complete!
    echo  Check the 'dist' folder for 3DTRF.exe
    echo  =======================================================
) else (
    echo.
    echo [ERROR] Build failed. Please check the logs above.
)

echo.
pause
exit /b %errorlevel%

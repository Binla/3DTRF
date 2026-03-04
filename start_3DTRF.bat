@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 3DTRF Launcher
color 0B

echo.
echo  =======================================================
echo     3DTRF Launcher v1.1
echo     3D Mesh to Solid (STEP) Converter
echo  =======================================================
echo.

:: Check Step Engine
if exist "%~dp0deps\python310\python.exe" (
    echo [SUCCESS] Step Engine Ready.
) else (
    echo [WARNING] Portable Step Engine not found.
    echo [INFO] UI will work, but STEP conversion will use limited fallback.
    echo.
)

:: Check for core dependencies in system python
echo [INFO] Checking core dependencies...
python -c "import flet; import trimesh; import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Missing dependencies. Installing...
    python -m pip install -r "%~dp0requirements.txt"
)

echo [SUCCESS] Dependencies verified.
echo [INFO] Launching 3DTRF...
echo.

:: Launch application
start "" python "%~dp0app.py"

echo [DONE] Application started. 
echo This window will close in 5 seconds...
timeout /t 5 >nul
exit /b 0

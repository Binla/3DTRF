@echo off
title 3DTRF Launcher
echo ========================================
echo   3DTRF - 3D Mesh to Solid Converter   
echo ========================================
echo Checking dependencies...
pip install -r requirements.txt
echo Starting application...
python app.py
pause

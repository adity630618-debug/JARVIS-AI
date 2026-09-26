@echo off
title J.A.R.V.I.S AI Assistant
cd /d "%~dp0"
echo ===================================================
echo Starting J.A.R.V.I.S System...
echo ===================================================
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] J.A.R.V.I.S encountered an issue.
    pause
)

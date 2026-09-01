@echo off
chcp 65001 >nul
title Item Farming Bot - Setup
cd /d "%~dp0"

echo =======================================================
echo    Install Item Farming Bot
echo =======================================================
echo.

REM Check Python
py --version >nul 2>&1
if %errorlevel%==0 (
    set PY=py
) else (
    python --version >nul 2>&1
    if %errorlevel%==0 (
        set PY=python
    ) else (
        echo [ERROR] Python not found
        echo Install Python first: https://www.python.org/downloads/
        echo Remember to tick "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
)

echo [1/2] Python found, updating pip...
%PY% -m pip install --upgrade pip

echo.
echo [2/2] Installing required libraries...
%PY% -m pip install -r requirements.txt

echo.
echo =======================================================
echo    Setup done!
echo    First time: run calibrate.bat to capture positions
echo    Run bot:    run.bat
echo =======================================================
echo.
pause

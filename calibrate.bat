@echo off
chcp 65001 >nul
title Smelt Bot - Calibrate
cd /d "%~dp0"

net session >nul 2>&1
if not %errorlevel%==0 (
    echo Requesting Administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

py --version >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)

%PY% bot\calibrate.py

echo.
pause

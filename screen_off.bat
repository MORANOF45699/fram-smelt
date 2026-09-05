@echo off
chcp 65001 >nul
title Screen Off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0screen_off.ps1"

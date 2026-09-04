@echo off
chcp 65001 >nul
title Smelt Bot - Config
cd /d "%~dp0"

py --version >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)

%PY% bot\set_config.py

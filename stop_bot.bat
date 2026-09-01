@echo off
chcp 65001 >nul
title Smelt Bot - Stop
cd /d "%~dp0"

REM ===== Need Administrator rights (bot runs elevated) =====
net session >nul 2>&1
if not %errorlevel%==0 (
    echo Requesting Administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo =======================================================
echo    Stopping all Smelt Bot processes
echo =======================================================
echo.

REM Kill only python processes running the bot scripts, not other python apps
powershell -NoProfile -Command ^
  "$p = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' or Name='python.exe' or Name='py.exe' or Name='pyw.exe'\" | Where-Object { $_.CommandLine -match 'smelt_main' };" ^
  "if ($p) { $p | ForEach-Object { Write-Host ('  killing PID ' + $_.ProcessId + '  ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue };" ^
  "  Start-Sleep -Milliseconds 600;" ^
  "  $left = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' or Name='python.exe'\" | Where-Object { $_.CommandLine -match 'smelt_main' };" ^
  "  if ($left) { Write-Host ''; Write-Host ('  WARNING: ' + $left.Count + ' still running') } else { Write-Host ''; Write-Host '  All bot processes stopped.' } }" ^
  "else { Write-Host '  No bot process found (nothing to stop).' }"

echo.
pause

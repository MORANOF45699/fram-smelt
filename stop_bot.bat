@echo off
chcp 65001 >nul
title Smelt Bot - Stop
cd /d "%~dp0"

REM ===== Administrator check =====
REM Not using "net session": it needs the Server service (LanmanServer).
REM On a PC with that service off the check never passes and the script
REM relaunches itself forever, which looks like the screen flickering.
REM %1 = --elevated means we already asked once. Never ask twice.
powershell -NoProfile -Command "exit ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
if %errorlevel%==1 goto :is_admin
if "%~1"=="--elevated" (
    echo [!] Could not get Administrator rights - running as normal user.
    echo     Key presses may not reach the game.
    timeout /t 3 >nul
    goto :is_admin
)
echo Requesting Administrator rights...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '--elevated' -Verb RunAs"
exit /b
:is_admin

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

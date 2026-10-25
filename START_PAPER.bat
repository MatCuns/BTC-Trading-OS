@echo off
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\first_run.ps1"
if errorlevel 1 echo Setup interrupted. Fix the displayed step and double-click START_PAPER.bat again.
pause

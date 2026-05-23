@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1

title RawLead — TG
echo.
echo  RawLead — TG-chaty (5 kanalov)
echo  Log: %CD%\data\radar.log
echo  Eto okno NE zakryvaj.
echo.

".venv\Scripts\python.exe" -u scripts\tg_main.py
echo.
echo  TG-monitor ostanovlen.
pause

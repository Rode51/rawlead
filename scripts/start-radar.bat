@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1

title RawLead — birzhi
echo.
echo  RawLead — birzhi FL.ru + Kwork
echo  Log: %CD%\data\radar.log
echo  Eto okno NE zakryvaj. V TG: Pauza / Start / Status
echo  Esli nuzhen i TG — zapusti start-radar-all.bat
echo.

".venv\Scripts\python.exe" -u src\main.py
echo.
echo  Radar ostanovlen.
pause

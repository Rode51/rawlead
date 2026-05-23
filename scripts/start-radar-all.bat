@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1

echo.
echo  RawLead — zapusk 2 okon: birzhi + TG
echo  Log: %CD%\data\radar.log
echo  Ne zapuskaj main.py v Cursor — budet Telegram 409
echo.

start "RawLead — birzhi" cmd /k "cd /d %CD% && title RawLead — birzhi && echo Birzhi FL+Kwork && echo. && .venv\Scripts\python.exe -u src\main.py"
start "RawLead — TG" cmd /k "cd /d %CD% && title RawLead — TG && echo Monitor 5 chatov && echo. && .venv\Scripts\python.exe -u scripts\tg_main.py"

echo  Otkryto 2 okna. Mozhno zakryt eto okno-zapuskatel.
timeout /t 4 >nul

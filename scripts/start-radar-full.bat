@echo off

chcp 65001 >nul

call "%~dp0_radar-env.bat"

if errorlevel 1 pause & exit /b 1



echo.

echo  FL Radar FULL — birzhi + TG (join vnutri TG)

echo  Join: vse TELETHON_MONITOR_ACCOUNTS v okne TG (TG_JOIN_IN_TG_MAIN=1)

echo  Log: %CD%\data\radar.log  join: data\tg_join.log

echo.



start "FL Radar — birzhi" cmd /k "cd /d %CD% && title FL Radar — birzhi && echo Birzhi FL+Kwork && echo. && .venv\Scripts\python.exe -u src\main.py"

start "FL Radar — TG" cmd /k "cd /d %CD% && title FL Radar — TG && echo Monitor + join && echo. && .venv\Scripts\python.exe -u scripts\tg_main.py"



echo  Otkryto 2 okna. Mozhno zakryt eto okno-zapuskatel.

timeout /t 4 >nul


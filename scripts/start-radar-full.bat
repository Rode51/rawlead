@echo off

chcp 65001 >nul

call "%~dp0_radar-env.bat"

if errorlevel 1 pause & exit /b 1



echo.

echo  FL Radar FULL — birzhi + TG + join supervisor

echo  acc1 join — vnutri okna TG (TG_JOIN_AUTO_ACC1)

echo  acc2/acc3/acc4 — odin daemon (TG_JOIN_DAEMON_ACCOUNTS)

echo  Log: %CD%\data\radar.log  join: data\tg_join.log

echo.



start "FL Radar — birzhi" cmd /k "cd /d %CD% && title FL Radar — birzhi && echo Birzhi FL+Kwork && echo. && .venv\Scripts\python.exe -u src\main.py"

start "FL Radar — TG" cmd /k "cd /d %CD% && title FL Radar — TG && echo Monitor + join acc1 && echo. && .venv\Scripts\python.exe -u scripts\tg_main.py"

start "FL Radar — join" cmd /k "cd /d %CD% && title FL Radar — join && echo Join supervisor daemon && echo. && .venv\Scripts\python.exe -u scripts\tg_join_daemon.py"



echo  Otkryto 3 okna. Mozhno zakryt eto okno-zapuskatel.

timeout /t 4 >nul

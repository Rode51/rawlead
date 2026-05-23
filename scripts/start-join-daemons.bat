@echo off

chcp 65001 >nul

call "%~dp0_radar-env.bat"

if errorlevel 1 pause & exit /b 1



echo.

echo  FL Radar — join supervisor (odin process, sm. TG_JOIN_DAEMON_ACCOUNTS)

echo  acc1 join — vnutri okna FL Radar — TG

echo.



start "FL Radar — join" cmd /k "cd /d %CD% && title FL Radar — join && echo Join supervisor && echo. && .venv\Scripts\python.exe -u scripts\tg_join_daemon.py"



echo  Otkryto 1 okno join. Mozhno zakryt eto okno-zapuskatel.

timeout /t 3 >nul

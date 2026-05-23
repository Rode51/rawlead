@echo off

chcp 65001 >nul

call "%~dp0_radar-env.bat"

if errorlevel 1 pause & exit /b 1



echo.

echo  DEPRECATED: join-supervisor ubran.

echo  Join vsekh acc — v okne FL Radar — TG (scripts\tg_main.py, TG_JOIN_IN_TG_MAIN=1).

echo.

pause

exit /b 2


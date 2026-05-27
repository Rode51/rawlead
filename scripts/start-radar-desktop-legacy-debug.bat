@echo off
chcp 65001 >nul
echo [debug] Legacy pult — окно не закроется, смотри ошибки ниже.
call "%~dp0start-radar-desktop.bat"
echo.
echo Exit code: %errorlevel%
pause

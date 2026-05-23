@echo off
REM Obshchaya proverka: venv + pip. Vyzov: call "%~dp0_radar-env.bat" ili iz papki scripts
set "RADAR_ROOT=%~dp0.."
if "%RADAR_ROOT:~-1%"=="\" set "RADAR_ROOT=%RADAR_ROOT:~0,-1%"
cd /d "%RADAR_ROOT%"

if not exist ".venv\Scripts\python.exe" (
    echo Oshibka: net .venv v %CD%
    echo   py -3.11 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Oshibka pip install — sm. docs\ops\RUN.md
    exit /b 1
)
exit /b 0

@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
start "" "%RADAR_ROOT%\.venv\Scripts\pythonw.exe" "%~dp0radar_desktop.py"
if errorlevel 1 (
  echo pythonw ne zapustilsya — probuem s oknom konsoli:
  "%RADAR_ROOT%\.venv\Scripts\python.exe" "%~dp0radar_desktop.py"
)
exit /b 0

@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
set "RADAR_PROFILE=site"
set "RADAR_CONTROL_PORT=18775"
set "VITE_RADAR_API=http://127.0.0.1:18775"

REM Всегда свежий API site (старый radar_control не знает RADAR_EXCHANGES_ENABLED)
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control; kill_all_radar_control(profile='site')" >nul 2>&1
timeout /t 1 /nobreak >nul
set "RADAR_PYW=%RADAR_ROOT%\.venv\Scripts\pythonw.exe"
if not exist "%RADAR_PYW%" (
  echo Oshibka: net pythonw: %RADAR_PYW%
  pause & exit /b 1
)
set "PYTHONPATH=%RADAR_ROOT%\.venv\Lib\site-packages"
start "" /B "%RADAR_PYW%" "%RADAR_ROOT%\scripts\radar_control.py" --profile site
timeout /t 2 /nobreak >nul

cd /d "%RADAR_ROOT%\desktop"
if not exist "node_modules\" (
  echo npm install v desktop\ ...
  call npm install
  if errorlevel 1 pause & exit /b 1
)

set "RADAR_RELEASE=%RADAR_ROOT%\desktop\src-tauri\target\release"
if exist "%RADAR_RELEASE%\desktop.exe" (
  set "RADAR_EXE=%RADAR_RELEASE%\desktop.exe"
) else if exist "%RADAR_RELEASE%\RawLead.exe" (
  set "RADAR_EXE=%RADAR_RELEASE%\RawLead.exe"
)
if defined RADAR_EXE (
  cd /d "%RADAR_ROOT%"
  start "" "%RADAR_EXE%"
  exit /b 0
)

echo Zapusk pulta SITE: npm run tauri dev (API :18775)
call npm run tauri dev
if errorlevel 1 pause
exit /b %errorlevel%

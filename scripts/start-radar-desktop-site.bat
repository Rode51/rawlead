@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
set "RADAR_PROFILE=site"
set "RADAR_CONTROL_PORT=18775"
set "VITE_RADAR_API=http://127.0.0.1:18775"

REM Зомби-lock после сбоя (pythonw выходит без release)
if exist "%RADAR_ROOT%\data\.radar_desktop_site.lock" del /f /q "%RADAR_ROOT%\data\.radar_desktop_site.lock" >nul 2>&1
if exist "%RADAR_ROOT%\data\.radar_ops_site.lock" del /f /q "%RADAR_ROOT%\data\.radar_ops_site.lock" >nul 2>&1

"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:18775/health', timeout=2)" >nul 2>&1
if not errorlevel 1 goto :launch_desktop

REM Порт мёртв — снять зомби API site (не трогать при живом /health выше)
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control; kill_all_radar_control(profile='site')" >nul 2>&1
ping -n 2 127.0.0.1 >nul

set "RADAR_PYW=%RADAR_ROOT%\.venv\Scripts\pythonw.exe"
if not exist "%RADAR_PYW%" (
  echo Oshibka: net pythonw: %RADAR_PYW%
  pause & exit /b 1
)
set "PYTHONPATH=%RADAR_ROOT%\.venv\Lib\site-packages"
cd /d "%RADAR_ROOT%"
REM /MIN, не /B — иначе API умирает вместе с cmd после VBS
start "" /MIN "%RADAR_PYW%" "%RADAR_ROOT%\scripts\radar_control.py" --profile site
ping -n 9 127.0.0.1 >nul
call :check_api_health
if errorlevel 1 (
  ping -n 4 127.0.0.1 >nul
  call :check_api_health
)
if errorlevel 1 (
  call :msgbox_api_fail "API site ne podnyalsya na :18775. Sm. data\radar_site.log"
  exit /b 1
)

:launch_desktop
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

:check_api_health
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:18775/health', timeout=5)" >nul 2>&1
exit /b %errorlevel%

:msgbox_api_fail
mshta "javascript:var s=new ActiveXObject('WScript.Shell'); s.Popup('%1',0,'RawLead Site',16);close()"
exit /b 0

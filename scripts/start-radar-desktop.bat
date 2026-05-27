@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
set "RADAR_PROFILE=legacy"
set "RADAR_CONTROL_PORT=18765"
set "VITE_RADAR_API=http://127.0.0.1:18765"

REM API уже жив — не убивать radar_control (двойной клик по ярлыку)
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:18765/health', timeout=2)" >nul 2>&1
if not errorlevel 1 goto desktop_only

REM Python API — убить все radar_control (venv + system), потом запустить чистый
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control; kill_all_radar_control(profile='legacy')" >nul 2>&1
timeout /t 1 /nobreak >nul
set "RADAR_PYW=%RADAR_ROOT%\.venv\Scripts\pythonw.exe"
if not exist "%RADAR_PYW%" (
  echo Oshibka: net pythonw: %RADAR_PYW%
  pause & exit /b 1
)
set "PYTHONPATH=%RADAR_ROOT%\.venv\Lib\site-packages"
start "" /B "%RADAR_PYW%" "%RADAR_ROOT%\scripts\radar_control.py" --profile legacy
timeout /t 2 /nobreak >nul

:desktop_only
REM Второй ярлык при живом API: убрать system-python воркеры, не трогая venv API
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_non_venv_radar_workers; kill_non_venv_radar_workers(profile='legacy')" >nul 2>&1
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
) else (
  set "RADAR_EXE="
)
if defined RADAR_EXE (
  cd /d "%RADAR_ROOT%"
  start "" "%RADAR_EXE%"
  exit /b 0
)
if exist "src-tauri\target\release\fl-radar-pult.exe" (
  start "" "src-tauri\target\release\fl-radar-pult.exe"
  exit /b 0
)
if exist "src-tauri\target\release\fl-radar.exe" (
  start "" "src-tauri\target\release\fl-radar.exe"
  exit /b 0
)
if exist "src-tauri\target\release\desktop.exe" (
  start "" "src-tauri\target\release\desktop.exe"
  exit /b 0
)

echo Zapusk pulta v rezhime razrabotki: npm run tauri dev
echo Nuzhen Rust: https://www.rust-lang.org/tools/install
call npm run tauri dev
if errorlevel 1 pause
exit /b %errorlevel%

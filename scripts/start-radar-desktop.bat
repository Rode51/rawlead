@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"

REM Python API (один экземпляр — lock в data\.radar_desktop.lock)
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:18765/health' -TimeoutSec 1).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  start "" /B "%RADAR_ROOT%\.venv\Scripts\pythonw.exe" "%RADAR_ROOT%\scripts\radar_control.py"
  timeout /t 1 /nobreak >nul
)

cd /d "%RADAR_ROOT%\desktop"
if not exist "node_modules\" (
  echo npm install v desktop\ ...
  call npm install
  if errorlevel 1 pause & exit /b 1
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

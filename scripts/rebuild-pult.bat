@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%\desktop"
if not exist "node_modules\" (
  echo npm install v desktop\ ...
  call npm install
  if errorlevel 1 pause & exit /b 1
)
echo [pult] npm run build + tauri build ...
call npm run build
if errorlevel 1 pause & exit /b 1
call npm run tauri build
if errorlevel 1 pause & exit /b 1
echo [pult] Gotovo: src-tauri\target\release\desktop.exe
echo.
echo Yarlyki na rabochij stol — TOLKO na VBS (ne na desktop.exe):
echo   Site:   scripts\start-radar-desktop-site.vbs
echo   Legacy: scripts\start-radar-desktop-legacy.vbs
echo Polnyj stopp: scripts\stop-radar-desktop-full.vbs
echo Sm. docs\ops\DESKTOP_LAUNCH.md
pause

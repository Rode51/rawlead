@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
echo [stop-full] site + legacy: radar_control + main/tg/join ...
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control; kill_all_radar_control(profile='site'); kill_all_radar_control(profile='legacy')" >nul 2>&1
timeout /t 2 /nobreak >nul
echo [stop-full] Gotovo.

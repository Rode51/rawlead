@echo off
chcp 65001 >nul
call "%~dp0_radar-env.bat"
if errorlevel 1 pause & exit /b 1
cd /d "%RADAR_ROOT%"
echo [stop-full] site + legacy: radar_control + main/tg/join ...
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,r'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control, kill_neon_legacy_consumers, release_stale_worker_locks, wait_radar_workers_stopped; kill_all_radar_control(profile='site'); kill_all_radar_control(profile='legacy'); kill_neon_legacy_consumers(); wait_radar_workers_stopped(); release_stale_worker_locks()" >nul 2>&1
ping -n 3 127.0.0.1 >nul
del /f /q "%RADAR_ROOT%\data\.radar_desktop_site.lock" >nul 2>&1
del /f /q "%RADAR_ROOT%\data\.radar_ops_site.lock" >nul 2>&1
del /f /q "%RADAR_ROOT%\data\.radar_desktop_legacy.lock" >nul 2>&1
del /f /q "%RADAR_ROOT%\data\.radar_ops_legacy.lock" >nul 2>&1
echo [stop-full] Gotovo.

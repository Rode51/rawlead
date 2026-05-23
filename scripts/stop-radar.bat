@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo Ostanovka procesov FL Radar (python iz papki uisness)...
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -match 'uisness\\\\(src\\\\main|scripts\\\\tg_main|scripts\\\\tg_join_daemon|scripts\\\\tg_join_queue)' } | ForEach-Object { Write-Host ('Kill PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); from health_check import try_release_stale_tg_main_lock; try_release_stale_tg_main_lock()"
)
echo.
echo Esli Status vse eshjo ne rabotaet — zakroy drugie bota s tem zhe tokenom (uvicorn i t.p.)
pause

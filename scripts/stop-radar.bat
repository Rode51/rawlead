@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo Ostanovka vorokerov RawLead (main, tg, join — bez API pul'ta)...
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and $_.CommandLine -match 'uisness[\\/](src[\\/]main|scripts[\\/]tg_main|scripts[\\/]tg_join_daemon|scripts[\\/]tg_join_queue)' } | ForEach-Object { Write-Host ('Kill PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); from process_guard import release_stale_worker_locks; release_stale_worker_locks()"
)
echo.
echo API pul'ta (radar_control) ne trogaem — tol'ko start-radar-desktop.vbs dlya polnogo restarta.
echo Esli Status vse eshjo ne rabotaet — zakroy drugie bota s tem zhe tokenom (uvicorn i t.p.)
pause

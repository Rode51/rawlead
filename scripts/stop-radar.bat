@echo off
chcp 65001 >nul
echo Ostanovka procesov FL Radar (python iz papki uisness)...
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -match 'uisness\\\\(src\\\\main|scripts\\\\tg_main|scripts\\\\tg_join_daemon|scripts\\\\tg_join_queue)' } | ForEach-Object { Write-Host ('Kill PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo.
echo Esli Status vse eshjo ne rabotaet — zakroy drugie bota s tem zhe tokenom (uvicorn i t.p.)
pause

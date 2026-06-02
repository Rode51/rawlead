@echo off
REM Локальный relay для Cursor: 127.0.0.1 -> пул прокси с автопереключением.
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Нет .venv
  exit /b 1
)
if not exist "data" mkdir data
echo Sync Cursor -> 127.0.0.1 (relay mode)...
.venv\Scripts\python.exe scripts\cursor_proxy_relay.py --sync-localhost
echo.
echo Запуск relay (оставь окно открытым или сверни)...
.venv\Scripts\pythonw.exe scripts\cursor_proxy_relay.py
exit /b 0

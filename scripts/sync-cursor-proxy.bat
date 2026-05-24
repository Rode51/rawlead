@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Нет .venv — создай venv в корне репо.
  exit /b 1
)
.venv\Scripts\python.exe scripts\sync_cursor_proxy.py
exit /b %ERRORLEVEL%

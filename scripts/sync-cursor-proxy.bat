@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Нет .venv — создай venv в корне репо.
  exit /b 1
)
REM По умолчанию: probe кандидатов, первый живой (CURSOR_PROXY_AUTO_FALLBACK=1)
.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --pick-live --disable-if-dead
exit /b %ERRORLEVEL%

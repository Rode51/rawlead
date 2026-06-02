@echo off
REM Подстраховка Cursor: probe всех прокси из .env → первый живой; иначе выкл. прокси.
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Нет .venv — создай venv в корне репо.
  exit /b 1
)
.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --pick-live --disable-if-dead
set RC=%ERRORLEVEL%
if %RC%==0 (
  echo.
  echo OK: Quit Cursor и открой снова.
) else if %RC%==2 (
  echo.
  echo Прокси мертвы — Cursor без прокси. Quit Cursor и открой снова.
) else (
  echo.
  echo Ошибка — см. .env CURSOR_PROXY_* и FOR_YOU.md
)
exit /b %RC%

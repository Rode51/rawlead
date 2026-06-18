@echo off
REM Убедиться что relay слушает 127.0.0.1:18777. exit 0 = OK, 1 = fail
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"

netstat -an | findstr ":18777" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo Relay OK.
  exit /b 0
)

echo Relay не запущен — стартую...
start "rawlead-relay" /MIN cmd /c "cd /d \"%ROOT%\" && .venv\Scripts\python.exe scripts\cursor_proxy_relay.py --sync-localhost && .venv\Scripts\pythonw.exe scripts\cursor_proxy_relay.py"

set /a N=0
:wait_loop
ping 127.0.0.1 -n 2 >nul
netstat -an | findstr ":18777" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo Relay OK.
  exit /b 0
)
set /a N+=1
if %N% LSS 15 goto wait_loop

echo Relay FAIL после 15 сек.
exit /b 1

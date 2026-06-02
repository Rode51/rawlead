@echo off
cd /d "%~dp0.."
echo Relay upstream pool probes:
.venv\Scripts\python.exe scripts\cursor_proxy_relay.py --probe-only
echo.
echo Cursor direct proxy probes:
.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --probe-only
exit /b %ERRORLEVEL%

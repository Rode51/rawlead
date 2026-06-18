@echo off
set YB="C:\Program Files\Yandex\YandexBrowser\Application\browser.exe"
set PROFILE=%~dp0..\data\yandex-debug-profile
if not exist %PROFILE% mkdir %PROFILE%
start "" %YB% --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%PROFILE%"
echo Yandex debug: http://127.0.0.1:9222
timeout /t 3 >nul
curl -s http://127.0.0.1:9222/json/version

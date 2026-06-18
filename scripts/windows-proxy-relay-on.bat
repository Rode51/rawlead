@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo [1/2] Relay 127.0.0.1:18777
call "%~dp0ensure-cursor-relay.bat"
if errorlevel 1 (
  echo Relay ne zapustilsya.
  pause & exit /b 1
)

echo [2/2] Windows: system proxy -^> 127.0.0.1:18777
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:18777" /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride /t REG_SZ /d "localhost;127.0.0.1;<local>" /f >nul

powershell -NoProfile -Command "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class P { [DllImport(\"wininet.dll\", SetLastError=true)] public static extern bool InternetSetOption(IntPtr h, int o, IntPtr b, int l); }'; [P]::InternetSetOption([IntPtr]::Zero, 39, [IntPtr]::Zero, 0) | Out-Null; [P]::InternetSetOption([IntPtr]::Zero, 37, [IntPtr]::Zero, 0) | Out-Null"

echo.
echo OK: ves PC cherez relay (vremenno).
echo Posle login zapusti: scripts\windows-proxy-relay-off.bat
echo.
pause

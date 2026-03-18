@echo off
:: MAVDP Startup Wrapper
:: This file allows for a "one-click" launch of the MAVDP system.

set SCRIPT_PATH=%~dp0START_MAVDP.ps1

powershell.exe -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"

if %ERRORLEVEL% neq 0 (
    echo [!] Error: MAVDP failed to start.
    pause
)

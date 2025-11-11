@echo off
REM Install Envy as Windows service using NSSM

echo Installing Envy as Windows service...
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Error: This script must be run as Administrator
    pause
    exit /b 1
)

set "BASE_DIR=%~dp0.."

REM Check if NSSM is available
where nssm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: NSSM not found.
    echo Please download NSSM from https://nssm.cc/download
    echo Extract nssm.exe to a directory in your PATH
    pause
    exit /b 1
)

REM Install service
echo Installing service...
nssm install Envy "%BASE_DIR%\venv\Scripts\python.exe" "%BASE_DIR%\envy_main.py --profile balanced --no-gui"
nssm set Envy AppDirectory "%BASE_DIR%"
nssm set Envy DisplayName "Envy Personal Assistant"
nssm set Envy Description "Envy AI Personal Assistant Service"
nssm set Envy Start SERVICE_AUTO_START

echo.
echo Envy service installed successfully!
echo.
echo To start: nssm start Envy
echo To stop:  nssm stop Envy
echo To remove: nssm remove Envy confirm
echo.
pause

@echo off
REM Install Envy as a Windows service using NSSM

echo Installing Envy AI Assistant as Windows service...
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script requires administrator privileges
    echo Please run as administrator
    pause
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0
set ENVY_DIR=%SCRIPT_DIR%..

echo Envy directory: %ENVY_DIR%
echo.

REM Check if NSSM is available
where nssm >nul 2>&1
if errorlevel 1 (
    echo NSSM not found. Downloading...
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to a directory in your PATH
    pause
    exit /b 1
)

REM Install service
echo Installing service...
nssm install Envy "%ENVY_DIR%\venv\Scripts\python.exe" "%ENVY_DIR%\envy_main.py" --config "%ENVY_DIR%\config\envy.yaml"

REM Configure service
nssm set Envy AppDirectory "%ENVY_DIR%"
nssm set Envy DisplayName "Envy AI Assistant"
nssm set Envy Description "Personal AI assistant with voice interaction"
nssm set Envy Start SERVICE_AUTO_START

echo.
echo Service installed successfully!
echo.
echo To start the service:
echo   net start Envy
echo.
echo To stop the service:
echo   net stop Envy
echo.
echo To remove the service:
echo   nssm remove Envy confirm
echo.

pause

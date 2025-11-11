@echo off
REM Install Envy as Windows service using NSSM
REM MIT License

echo =========================================
echo Installing Envy as Windows service
echo =========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ This script requires administrator privileges
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set paths
set SERVICE_NAME=Envy
set PROJECT_DIR=%~dp0..
set PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe
set MAIN_SCRIPT=%PROJECT_DIR%\main.py

echo Service name: %SERVICE_NAME%
echo Project directory: %PROJECT_DIR%
echo.

REM Check if NSSM is installed
where nssm >nul 2>&1
if errorlevel 1 (
    echo ❌ NSSM is not installed
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to a directory in your PATH
    pause
    exit /b 1
)

echo ✓ NSSM found

REM Install service
echo Installing service...
nssm install %SERVICE_NAME% "%PYTHON_EXE%" "%MAIN_SCRIPT%" --profile balanced

REM Configure service
nssm set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
nssm set %SERVICE_NAME% DisplayName "Envy Personal AI Assistant"
nssm set %SERVICE_NAME% Description "Voice-activated AI assistant with local models"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

echo.
echo =========================================
echo ✅ Service installed successfully!
echo =========================================
echo.
echo Control Envy with:
echo   Start:  net start %SERVICE_NAME%
echo   Stop:   net stop %SERVICE_NAME%
echo   Status: sc query %SERVICE_NAME%
echo.
echo Or use Windows Services (services.msc)
echo.
pause

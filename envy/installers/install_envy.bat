@echo off
REM Install Envy Personal Assistant on Windows

echo ========================================
echo Envy Personal Assistant Installer
echo ========================================
echo.

REM Check for Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "BASE_DIR=%SCRIPT_DIR%.."

REM Create virtual environment
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    echo Virtual environment created
) else (
    echo Virtual environment exists
)

echo.
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Installing dependencies...
cd "%BASE_DIR%"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo.
echo Dependencies installed
echo.

REM Create directories
echo Creating directories...
if not exist "%BASE_DIR%\logs" mkdir "%BASE_DIR%\logs"
if not exist "%BASE_DIR%\data" mkdir "%BASE_DIR%\data"
if not exist "%BASE_DIR%\workspace" mkdir "%BASE_DIR%\workspace"
if not exist "%BASE_DIR%\artifacts\tests" mkdir "%BASE_DIR%\artifacts\tests"
if not exist "%BASE_DIR%\models" mkdir "%BASE_DIR%\models"
echo Directories created
echo.

REM Create run scripts
echo Creating run scripts...

echo @echo off > "%BASE_DIR%\run_envy_local.bat"
echo set "SCRIPT_DIR=%%~dp0" >> "%BASE_DIR%\run_envy_local.bat"
echo call "%%SCRIPT_DIR%%venv\Scripts\activate.bat" >> "%BASE_DIR%\run_envy_local.bat"
echo cd "%%SCRIPT_DIR%%" >> "%BASE_DIR%\run_envy_local.bat"
echo python envy_main.py %%* >> "%BASE_DIR%\run_envy_local.bat"

echo @echo off > "%BASE_DIR%\start-envy.bat"
echo set "SCRIPT_DIR=%%~dp0" >> "%BASE_DIR%\start-envy.bat"
echo call "%%SCRIPT_DIR%%venv\Scripts\activate.bat" >> "%BASE_DIR%\start-envy.bat"
echo cd "%%SCRIPT_DIR%%" >> "%BASE_DIR%\start-envy.bat"
echo python envy_main.py --profile balanced >> "%BASE_DIR%\start-envy.bat"

echo Run scripts created
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run Envy:
echo   run_envy_local.bat --profile balanced
echo.
echo Or simply:
echo   start-envy.bat
echo.
echo Dashboard will be available at: http://127.0.0.1:8080
echo.
echo Note: You'll need to download models manually.
echo Run: installers\download_models.sh (or download models from links in docs)
echo.
pause

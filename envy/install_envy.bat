@echo off
REM Envy Installation Script for Windows
REM MIT License

echo =========================================
echo ^🤖 Envy Personal Assistant - Installer
echo =========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)
echo ✓ Python found

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed
    pause
    exit /b 1
)
echo ✓ pip found

REM Create virtual environment
echo.
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo.
echo [4/5] Installing Python dependencies...
echo This may take several minutes...
pip install -r requirements.txt

REM Create directories
echo.
echo [5/5] Setting up directories...
if not exist "artifacts\logs" mkdir artifacts\logs
if not exist "artifacts\tests" mkdir artifacts\tests
if not exist "artifacts\research" mkdir artifacts\research
if not exist "models" mkdir models

echo.
echo =========================================
echo ✅ Installation Complete!
echo =========================================
echo.
echo To start Envy:
echo   1. Activate virtual environment: venv\Scripts\activate.bat
echo   2. Run: python main.py
echo.
echo Or use the quick-start script: run_envy_local.bat
echo.
echo Web dashboard will be available at: http://localhost:8080
echo.
echo Note: Download models by running: scripts\download_models.bat
echo       Or enable remote API fallback in config\envy.yaml
echo.
pause

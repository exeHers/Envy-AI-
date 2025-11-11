@echo off
REM Envy installer for Windows

echo ==========================================
echo Envy Personal Assistant - Windows Installer
echo ==========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.10+ is required
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Download VOSK model if not present
if not exist "models\vosk-model-small-en-us-0.15" (
    echo Downloading VOSK model...
    mkdir models 2>nul
    cd models
    curl -L -o vosk-model-small-en-us-0.15.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    powershell -Command "Expand-Archive -Path vosk-model-small-en-us-0.15.zip -DestinationPath . -Force"
    del vosk-model-small-en-us-0.15.zip
    cd ..
)

REM Create necessary directories
echo Creating directories...
mkdir artifacts\tests 2>nul
mkdir artifacts\tts 2>nul
mkdir logs 2>nul

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo To run Envy:
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
echo Or use the run script:
echo   run_envy_local.bat
echo.

pause

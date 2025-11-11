@echo off
REM install_envy.bat - Installer for Envy Personal Assistant (Windows)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set ENVY_DIR=%SCRIPT_DIR%
set VENV_DIR=%ENVY_DIR%venv

echo ==========================================
echo Envy Personal Assistant - Installer
echo ==========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required
    exit /b 1
)

echo Creating virtual environment...
python -m venv "%VENV_DIR%"

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo Installing dependencies...
pip install -r "%ENVY_DIR%requirements.txt" || (
    echo Installing core dependencies...
    pip install sounddevice vosk openai-whisper pyttsx3 fastapi uvicorn websockets pyyaml requests numpy psutil
)

echo Creating models directory...
if not exist "%ENVY_DIR%models" mkdir "%ENVY_DIR%models"

echo Creating artifacts directory...
if not exist "%ENVY_DIR%artifacts\tests" mkdir "%ENVY_DIR%artifacts\tests"
if not exist "%ENVY_DIR%artifacts\tts" mkdir "%ENVY_DIR%artifacts\tts"
if not exist "%ENVY_DIR%artifacts\models" mkdir "%ENVY_DIR%artifacts\models"

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo To run Envy:
echo   cd %ENVY_DIR%
echo   venv\Scripts\activate
echo   run_envy_local.bat
echo.

pause

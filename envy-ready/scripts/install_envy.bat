@echo off
REM install_envy.bat - Windows installer for Envy Personal Assistant
setlocal enabledelayedexpansion

set ENVY_DIR=%~dp0
set VENV_DIR=%ENVY_DIR%venv
set PYTHON_CMD=python

echo ==========================================
echo Envy Personal Assistant - Installer
echo ==========================================

REM Check Python
echo Checking Python...
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
if not exist "%VENV_DIR%" (
    %PYTHON_CMD% -m venv "%VENV_DIR%"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo Installing dependencies...
cd /d "%ENVY_DIR%"
pip install -r requirements.txt

REM Create directories
echo Creating directories...
if not exist "models" mkdir models
if not exist "artifacts\tests" mkdir artifacts\tests
if not exist "artifacts\tts-output" mkdir artifacts\tts-output
if not exist "config" mkdir config
if not exist "skills" mkdir skills

REM Download models if requested
if "%1"=="--local-demo" (
    echo Downloading models...
    if exist "scripts\download_models.bat" (
        call scripts\download_models.bat
    ) else (
        echo Model download script not found.
    )
)

REM Create run script
echo Creating run script...
(
echo @echo off
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo python main.py %%*
) > "%ENVY_DIR%run_envy_local.bat"

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo To start Envy:
echo   run_envy_local.bat
echo.
pause

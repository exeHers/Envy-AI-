@echo off
REM Install script for Envy Personal Assistant (Windows)

setlocal enabledelayedexpansion

set ENVY_DIR=%~dp0envy
set VENV_DIR=%ENVY_DIR%\venv
set PROFILE=%1
if "%PROFILE%"=="" set PROFILE=balanced

echo ==========================================
echo Envy Personal Assistant - Installer
echo ==========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.10+ is required
    exit /b 1
)

echo Python version:
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
echo.
echo Installing dependencies...
cd /d "%ENVY_DIR%"
pip install -r requirements.txt

REM Create directories
echo.
echo Creating directories...
if not exist "%ENVY_DIR%\artifacts" mkdir "%ENVY_DIR%\artifacts"
if not exist "%ENVY_DIR%\workspace" mkdir "%ENVY_DIR%\workspace"
if not exist "%ENVY_DIR%\models" mkdir "%ENVY_DIR%\models"

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo To start Envy:
echo   cd %ENVY_DIR%
echo   %VENV_DIR%\Scripts\activate.bat
echo   python envy.py --profile %PROFILE%
echo.

pause

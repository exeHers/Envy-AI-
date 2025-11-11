@echo off
REM Run Envy locally (Windows)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set ENVY_DIR=%SCRIPT_DIR%
set VENV_DIR=%ENVY_DIR%\venv
set PROFILE=balanced
set NO_GUI=

REM Parse arguments
:parse_args
if "%~1"=="" goto :end_parse
if "%~1"=="--profile" (
    set PROFILE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--no-gui" (
    set NO_GUI=--no-gui
    shift
    goto :parse_args
)
shift
goto :parse_args

:end_parse

REM Activate virtual environment
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo Virtual environment not found. Run install_envy.bat first.
    exit /b 1
)

REM Change to envy directory
cd /d "%ENVY_DIR%"

REM Run Envy
python envy.py --profile %PROFILE% %NO_GUI%

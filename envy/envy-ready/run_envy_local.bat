@echo off
REM run_envy_local.bat - Run Envy locally (Windows)

setlocal

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Parse arguments
set PROFILE=balanced
set NO_GUI=false

:parse_args
if "%1"=="" goto run
if "%1"=="--profile" (
    set PROFILE=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--no-gui" (
    set NO_GUI=true
    shift
    goto parse_args
)
shift
goto parse_args

:run
echo Starting Envy with profile: %PROFILE%
python src\main.py --profile %PROFILE% --config config\envy.yaml

pause

@echo off
REM Run Envy locally on Windows

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Parse arguments
set PROFILE=balanced
set NO_GUI=

:parse_args
if "%1"=="" goto run
if "%1"=="--profile" (
    set PROFILE=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--no-gui" (
    set NO_GUI=--no-gui
    shift
    goto parse_args
)
shift
goto parse_args

:run
python main.py --profile %PROFILE% %NO_GUI%

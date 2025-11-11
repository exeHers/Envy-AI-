@echo off
set ROOT_DIR=%~dp0
if "%ROOT_DIR:~-1%"=="\" set ROOT_DIR=%ROOT_DIR:~0,-1%
set VENV_DIR=%ROOT_DIR%\.venv
set PROFILE=balanced
set GUI_FLAG=

:parse
if "%~1"=="" goto run
if "%~1"=="--profile" (
    set PROFILE=%~2
    shift
    shift
    goto parse
)
if "%~1"=="--no-gui" (
    set GUI_FLAG=--no-gui
    shift
    goto parse
)
if "%~1"=="--help" (
    echo Usage: start-envy.bat [--profile name] [--no-gui]
    exit /b 0
)
echo Unknown option %1
exit /b 1

:run
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment missing. Run install_envy.bat first.
    exit /b 1
)
call "%VENV_DIR%\Scripts\activate.bat"
python -m envy.main start --profile %PROFILE% %GUI_FLAG%

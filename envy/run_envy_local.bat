@echo off
setlocal

set PROFILE=balanced
set DASHBOARD=
set AUDIO=

:parse
if "%~1"=="" goto run
if "%~1"=="--profile" (
    set PROFILE=%~2
    shift
    shift
    goto parse
)
if "%~1"=="--dashboard" (
    set DASHBOARD=--dashboard
    shift
    goto parse
)
if "%~1"=="--no-dashboard" (
    set DASHBOARD=
    shift
    goto parse
)
if "%~1"=="--audio-file" (
    set AUDIO=--audio-file %~2
    shift
    shift
    goto parse
)
shift
goto parse

:run
set REPO_ROOT=%~dp0
set VENV_DIR=%REPO_ROOT%\.venv

if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Run install_envy.bat first.
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
set PYTHONPATH=%REPO_ROOT%
python -m envy.cli run --profile %PROFILE% %DASHBOARD% %AUDIO%

endlocal

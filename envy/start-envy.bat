@echo off
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%\.venv"

if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
)

if "%ENVY_PROFILE%"=="" (
    set "ENVY_PROFILE=balanced"
)

if "%ENVY_CONFIG_PATH%"=="" (
    set "ENVY_CONFIG_PATH=%SCRIPT_DIR%config\envy.yaml"
)

set "ENVY_PROFILE=%ENVY_PROFILE%"
set "ENVY_CONFIG_PATH=%ENVY_CONFIG_PATH%"

python -m envy.scripts.process_manager start --profile "%ENVY_PROFILE%" --config "%ENVY_CONFIG_PATH%" %*

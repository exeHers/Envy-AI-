@echo off
set "ROOT=%~dp0"
set "PROFILE=balanced"
set "NO_GUI=0"

:parse
if "%~1"=="" goto done
if "%~1"=="--profile" (
    set "PROFILE=%~2"
    shift
    shift
    goto parse
)
if "%~1"=="--no-gui" (
    set "NO_GUI=1"
    shift
    goto parse
)
if "%~1"=="--help" (
    echo Usage: run_envy_local.bat [--profile NAME] [--no-gui]
    exit /b 0
)
shift
goto parse

:done
set "CMD_ARGS=--profile %PROFILE% --config %ROOT%\config\envy.yaml"
if %NO_GUI%==1 set CMD_ARGS=%CMD_ARGS% --no-dashboard

call "%ROOT%\start-envy.bat" %CMD_ARGS%
